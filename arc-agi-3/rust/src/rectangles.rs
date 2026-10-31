//! Lossless horizontal-run rectangles for observation-only template inference.
use rayon::prelude::*;
use std::collections::BTreeMap;

fn rectangles(a: &[u8], h: usize, w: usize) -> Vec<[u32; 5]> {
    let mut active = BTreeMap::new();
    let mut out = Vec::new();
    for y in 0..h {
        let mut current = BTreeMap::new();
        let mut x = 0;
        while x < w {
            let start = x;
            let color = a[y * w + x];
            while x < w && a[y * w + x] == color {
                x += 1;
            }
            let key = (color, start, x);
            current.insert(key, active.get(&key).copied().unwrap_or(y));
        }
        for (&(color, left, right), &top) in &active {
            if !current.contains_key(&(color, left, right)) {
                out.push([
                    top as u32,
                    y as u32,
                    left as u32,
                    right as u32,
                    color as u32,
                ]);
            }
        }
        active = current;
    }
    for ((color, left, right), top) in active {
        out.push([
            top as u32,
            h as u32,
            left as u32,
            right as u32,
            color as u32,
        ]);
    }
    out.sort_unstable();
    out
}

/// Output capacity is count*h*w*5 u32s; each record is top,bottom,left,right,color.
/// # Safety
/// Input/output buffers must be aligned, non-overlapping, live, and at least
/// input_len bytes/output_len u32s/count lengths respectively.
#[no_mangle]
pub unsafe extern "C" fn arc3_rect_batch(
    input: *const u8,
    input_len: usize,
    h: usize,
    w: usize,
    count: usize,
    output: *mut u32,
    output_len: usize,
    lengths: *mut u32,
    parallel: u8,
) -> i32 {
    if h == 0 || w == 0 || h > 512 || w > 512 || count > 4096 {
        return -1;
    }
    if count == 0 {
        return 0;
    }
    let pixels = h * w * count;
    if input.is_null()
        || output.is_null()
        || lengths.is_null()
        || input_len != pixels
        || output_len < pixels * 5
    {
        return -1;
    }
    std::panic::catch_unwind(|| {
        let frames = unsafe { std::slice::from_raw_parts(input, input_len) };
        let rows: Vec<_> = if parallel != 0 && count > 1 {
            frames
                .par_chunks_exact(h * w)
                .map(|f| rectangles(f, h, w))
                .collect()
        } else {
            frames
                .chunks_exact(h * w)
                .map(|f| rectangles(f, h, w))
                .collect()
        };
        let dest = unsafe { std::slice::from_raw_parts_mut(output, output_len) };
        let sizes = unsafe { std::slice::from_raw_parts_mut(lengths, count) };
        for (i, row) in rows.iter().enumerate() {
            sizes[i] = row.len() as u32;
            for (j, r) in row.iter().enumerate() {
                dest[i * h * w * 5 + j * 5..i * h * w * 5 + j * 5 + 5].copy_from_slice(r);
            }
        }
    })
    .map_or(-2, |_| 0)
}
