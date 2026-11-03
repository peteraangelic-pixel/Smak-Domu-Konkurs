// jsdig — Rust + Rayon: równoległe kopanie bundle'ów JS (offline, poza limitem 5 req/s).
// Użycie: jsdig <katalog-z-plikami-js>  → JSONL na stdout {file, pattern, count, sample}
// Cel sprzętowy: Ryzen 9 5950X (16C/32T) — setki MB JS w sekundy.
use rayon::prelude::*;
use regex::Regex;
use std::collections::VecDeque;
use std::fs;
use std::path::{Path, PathBuf};

fn collect_files(dir: &Path, out: &mut Vec<PathBuf>) {
    if let Ok(rd) = fs::read_dir(dir) {
        for e in rd.flatten() {
            let p = e.path();
            if p.is_dir() {
                collect_files(&p, out);
            } else if let Some(ext) = p.extension().and_then(|e| e.to_str()) {
                if matches!(ext, "js" | "mjs" | "map" | "json") {
                    out.push(p);
                }
            }
        }
    }
}

fn esc(s: &str) -> String {
    let mut o = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '"' => o.push_str("\\\""),
            '\\' => o.push_str("\\\\"),
            '\n' | '\r' | '\t' => o.push(' '),
            c if (c as u32) < 0x20 => {}
            c => o.push(c),
        }
    }
    o.chars().take(200).collect()
}

const PATTERNS: &[(&str, &str)] = &[
    ("api_path", r#"[\"'](/api/[A-Za-z0-9/_.\-]{2,80})[\"']"#),
    ("v_path", r#"[\"'](/v[0-9]/[A-Za-z0-9/_.\-]{2,80})[\"']"#),
    ("internal_url", r#"(?i)https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|[^/\"']*\.internal|[^/\"']*\.local|[^/\"']*azurewebsites\.net|[^/\"']*blob\.core\.windows\.net|[^/\"']*database\.windows\.net)"#),
    ("jwt", r#"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}"#),
    ("aws_key", r#"AKIA[0-9A-Z]{16}"#),
    ("github_tok", r#"gh[pousr]_[A-Za-z0-9]{30,40}"#),
    ("google_key", r#"AIza[0-9A-Za-z_\-]{35}"#),
    ("slack_tok", r#"xox[baprs]-[A-Za-z0-9\-]{10,}"#),
    ("privkey", r#"-----BEGIN [A-Z ]*PRIVATE KEY-----"#),
    ("next_public", r#"NEXT_PUBLIC_[A-Z_]{2,40}\s*[:=]\s*[\"']([^\"']{1,120})[\"']"#),
    ("sourcemap_ref", r#"//#\s*sourceMappingURL=([^\s]+\.map)"#),
    ("graphql", r#"[\"'](?:/graphql|/api/graphql[^\"']*)[\"']"#),
    ("websocket", r#"wss?://[A-Za-z0-9.\-_:]{3,80}[^\s"<>]{0,60}"#),
    ("bearer_hdr", r#"[Bb]earer\s+[A-Za-z0-9_\-\.=]{20,80}"#),
    ("apikey_word", r#"(?i)[\"'](?:api[_-]?key|apikey|secret|token|password)[\"']\s*[:=]\s*[\"']([A-Za-z0-9_\-\.]{8,60})[\"']"#),
    ("email_pl", r#"[A-Za-z0-9._%+\-]+@(?:nask\.pl|dns\.pl|cert\.pl|nask\.gov\.pl)"#),
];

fn main() {
    let arg = std::env::args().nth(1).unwrap_or_else(|| ".".into());
    let mut files = Vec::new();
    collect_files(Path::new(&arg), &mut files);

    let regexes: Vec<(String, Regex)> = PATTERNS
        .iter()
        .filter_map(|(n, p)| Regex::new(p).ok().map(|r| (n.to_string(), r)))
        .collect();

    let results: Vec<String> = files
        .par_iter()
        .filter_map(|p| {
            let data = fs::read_to_string(p).ok()?;
            let mut lines = Vec::new();
            for (name, rx) in &regexes {
                let mut hits: Vec<String> = Vec::new();
                for cap in rx.captures_iter(&data) {
                    let s = cap.get(1).map(|m| m.as_str()).unwrap_or(cap.get(0).map(|m| m.as_str()).unwrap_or(""));
                    let s = esc(s);
                    if !s.is_empty() && !hits.contains(&s) {
                        hits.push(s);
                    }
                    if hits.len() >= 40 {
                        break;
                    }
                }
                if !hits.is_empty() {
                    lines.push(format!(
                        "{{\"file\":\"{}\",\"pattern\":\"{}\",\"count\":{},\"sample\":[{}]}}",
                        esc(&p.display().to_string()),
                        name,
                        hits.len(),
                        hits.iter().take(8).map(|h| format!("\"{}\"", h)).collect::<Vec<_>>().join(",")
                    ));
                }
            }
            if lines.is_empty() {
                None
            } else {
                Some(lines.join("\n"))
            }
        })
        .collect();

    for r in results {
        println!("{}", r);
    }
    eprintln!("jsdig-rs: {} plików przetworzonych", files.len());
}
