//! C ABI for batched click candidates. Buffers are allocated by the caller.
use rayon::prelude::*;
use std::collections::HashSet;

fn candidates(frame: &[u8], h: usize, w: usize, limit: usize) -> Vec<(u32, u32)> {
    if limit == 0 {
        return Vec::new();
    }
    let mut visited = vec![false; frame.len()];
    let mut blobs = Vec::new();
    for y0 in 0..h {
        for x0 in 0..w {
            let color = frame[y0 * w + x0];
            if color == 0 || visited[y0 * w + x0] {
                continue;
            }
            let mut stack = vec![(y0 as isize, x0 as isize)];
            let mut points = Vec::new();
            while let Some((y, x)) = stack.pop() {
                if y < 0 || x < 0 || y >= h as isize || x >= w as isize {
                    continue;
                }
                let index = y as usize * w + x as usize;
                if visited[index] || frame[index] != color {
                    continue;
                }
                visited[index] = true;
                points.push((y as usize, x as usize));
                stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]);
            }
            if points.len() >= 2 {
                blobs.push(points);
            }
        }
    }
    // Stable order matches Python when component sizes tie.
    blobs.sort_by_key(|points| std::cmp::Reverse(points.len()));
    let mut seen = HashSet::new();
    let mut result = Vec::new();
    for points in blobs {
        let cy = points.iter().map(|p| p.0).sum::<usize>() / points.len();
        let cx = points.iter().map(|p| p.1).sum::<usize>() / points.len();
        let mut low = points[0];
        let mut high = points[0];
        for &p in &points {
            if p.0 < low.0 {
                low = p;
            }
            if p.0 > high.0 {
                high = p;
            }
        }
        for (y, x) in [(cy, cx), low, high] {
            let point = (x as u32, y as u32);
            if seen.insert(point) {
                result.push(point);
            }
            if result.len() >= limit {
                return result;
            }
        }
    }
    result
}

/// Return 0 on success, -1 on invalid dimensions/buffers, -2 on a caught panic.
///
/// # Safety
/// The input must reference input_len readable bytes. Output and lengths must
/// reference output_len writable u32s and count writable u32s respectively.
/// All buffers must be live, aligned, and non-overlapping for the entire call.
#[no_mangle]
pub unsafe extern "C" fn arc3_blob_batch(
    input: *const u8,
    input_len: usize,
    h: usize,
    w: usize,
    count: usize,
    limit: usize,
    output: *mut u32,
    output_len: usize,
    lengths: *mut u32,
    parallel: u8,
) -> i32 {
    if h == 0 || w == 0 || h > 512 || w > 512 || count > 4096 || limit > h * w {
        return -1;
    }
    if count == 0 {
        return 0;
    }
    if limit == 0
        || input.is_null()
        || output.is_null()
        || lengths.is_null()
        || input_len != h * w * count
        || output_len < count * limit * 2
    {
        return -1;
    }
    std::panic::catch_unwind(|| {
        let frames = unsafe { std::slice::from_raw_parts(input, input_len) };
        let compute = |frame: &[u8]| candidates(frame, h, w, limit);
        let rows: Vec<_> = if parallel != 0 && count > 1 {
            frames.par_chunks_exact(h * w).map(compute).collect()
        } else {
            frames.chunks_exact(h * w).map(compute).collect()
        };
        let destination = unsafe { std::slice::from_raw_parts_mut(output, output_len) };
        let sizes = unsafe { std::slice::from_raw_parts_mut(lengths, count) };
        for (index, row) in rows.iter().enumerate() {
            sizes[index] = row.len() as u32;
            for (j, &(x, y)) in row.iter().enumerate() {
                destination[index * limit * 2 + j * 2] = x;
                destination[index * limit * 2 + j * 2 + 1] = y;
            }
        }
    })
    .map_or(-2, |_| 0)
}
