"""Reproduce peer synthetic safety probes with16 processes and Rust FFI.

These declared synthetic rules are not the hidden competition distribution.
"""
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def run(job):
    name,family=job
    path=ROOT/('template_gated_transfer.py' if name=='gated' else 'template_transfer.py')
    spec=importlib.util.spec_from_file_location('peer_probe',ROOT/'peer-review-20261031/template_false_positive_probe.py')
    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    policy=probe.load_policy(str(path))
    from native_rectangles import NativeRectangles
    policy.infer_copy_action.__defaults__=(None,NativeRectangles())
    fired,correct=probe.measure(policy,family,300)
    return {'policy':name,'family':family,'trials':300,'fired':fired,'correct':correct}


if __name__=='__main__':
    for key in ('RAYON_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
    jobs=[(p,f) for p in ('original','gated') for f in ('copy','rotate','invert','random')]
    with ProcessPoolExecutor(max_workers=16) as pool: rows=list(pool.map(run,jobs))
    out=ROOT/'navigation-20261031/gated-safety.json'
    out.write_text(json.dumps({'workers':16,'backend':'Rust FFI','rows':rows},indent=2),encoding='utf8')
    print(json.dumps(rows,indent=2))
