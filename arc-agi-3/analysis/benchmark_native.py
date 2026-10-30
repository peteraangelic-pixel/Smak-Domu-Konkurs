"""Check Python/Rust candidate parity and time the complete FFI call."""
import json
import os
from pathlib import Path
import re
import time

import numpy as np

from native_kernels import NativeKernels
from sweep2 import blob_candidates, load_game, frame_of, ActionInput, RESET


def timed(function, repeats=3):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        function()
        times.append(time.perf_counter() - start)
    return min(times)


if __name__ == '__main__':
    os.environ['RAYON_NUM_THREADS'] = '16'
    root = Path(__file__).resolve().parents[1]
    kernels = NativeKernels()
    frames = []
    for path in sorted((root / 'games/environment_files').rglob('*.py')):
        name = re.search(r'^class (\w+)\(ARCBaseGame\)', path.read_text(encoding='utf8'), re.M)[1]
        game = load_game(str(path), name)
        frames.append(frame_of(game.perform_action(ActionInput(id=RESET), raw=True)))
    rng = np.random.default_rng(20261030)
    random_frames = rng.integers(0, 5, (64, 64, 64), dtype=np.uint8)
    batch = np.stack(frames)
    checks = 0
    for inputs in (batch, random_frames):
        for limit in (1, 3, 28):
            expected = [blob_candidates(frame, limit) for frame in inputs]
            serial = kernels.blob_batch(inputs, limit, parallel=False)
            parallel = kernels.blob_batch(inputs, limit, parallel=True)
            assert expected == serial == parallel, f'Candidate mismatch at limit {limit}'
            checks += len(inputs)
    results = {'parity_cases': checks, 'rayon_threads': 16, 'timings': {}}
    for name, inputs in (('public_initial_frames', batch), ('random_frames', random_frames)):
        python = timed(lambda: [blob_candidates(frame, 28) for frame in inputs])
        ffi = timed(lambda: [kernels.blob_candidates(frame, 28) for frame in inputs])
        rayon = timed(lambda: kernels.blob_batch(inputs, 28, parallel=True))
        results['timings'][name] = {
            'frames': len(inputs), 'python_ms': python * 1000,
            'rust_ffi_serial_ms': ffi * 1000, 'rust_ffi_rayon16_ms': rayon * 1000,
            'serial_speedup': python / ffi, 'rayon_speedup': python / rayon,
        }
    output = Path(__file__).with_name('native-benchmark-results.json')
    output.write_text(json.dumps(results, indent=2), encoding='utf8')
    print(json.dumps(results, indent=2))
