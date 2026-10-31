"""Check portable/Rust equivalence and measure rectangle extraction including FFI."""
import json
import os
from pathlib import Path
import time
import numpy as np
from native_rectangles import NativeRectangles
from template_transfer import rectangles,infer_copy_action


if __name__=='__main__':
    os.environ['RAYON_NUM_THREADS']='16'
    root=Path(__file__).with_name('causal-agent-20261031')
    initial=np.array(json.loads((root/'ft09-initial-grid.json').read_text()),dtype=np.uint8)
    rng=np.random.default_rng(947)
    frames=[rng.integers(0,16,(64,64),dtype=np.uint8) for _ in range(32)]
    frames += [np.rot90(rng.permutation(16).astype(np.uint8)[initial],i%4).copy() for i in range(32)]
    native=NativeRectangles()
    rust=native.batch(np.array(frames),parallel=True)
    assert all(sorted(rectangles(a))==b for a,b in zip(frames,rust))
    for frame in frames[32:]:
        assert infer_copy_action(frame)==infer_copy_action(frame,extract_rectangles=native)
    sample=np.repeat(initial[None],256,axis=0)
    timings={}
    t=time.perf_counter();portable=[rectangles(a) for a in sample];timings['numpy_python_seconds']=time.perf_counter()-t
    t=time.perf_counter();serial=native.batch(sample,parallel=False);timings['rust_serial_ffi_seconds']=time.perf_counter()-t
    t=time.perf_counter();parallel=native.batch(sample,parallel=True);timings['rust_rayon16_ffi_seconds']=time.perf_counter()-t
    assert all(sorted(a)==b==c for a,b,c in zip(portable,serial,parallel))
    report={'equivalent_frames':len(frames),'equivalent_decisions':32,'benchmark_frames':len(sample),
            **timings,'rayon_threads':16,
            'speedup_including_ffi':timings['numpy_python_seconds']/timings['rust_rayon16_ffi_seconds'],
            'qualification':'Rectangle feature kernel only; excludes planning,game engine and LLM. Includes ctypes buffers and Python result conversion.'}
    (root/'structural-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))
