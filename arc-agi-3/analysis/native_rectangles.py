"""Strict ctypes FFI to the isolated Rust/Rayon observation kernel."""
import ctypes
from pathlib import Path
import sys
import numpy as np


class NativeRectangles:
    def __init__(self):
        name='arc3.dll' if sys.platform=='win32' else 'libarc3.dylib' if sys.platform=='darwin' else 'libarc3.so'
        self.library=ctypes.CDLL(str(Path(__file__).resolve().parents[1]/'rust/target/structural/release'/name))
        self.fn=self.library.arc3_rect_batch
        self.fn.argtypes=[ctypes.POINTER(ctypes.c_uint8),ctypes.c_size_t,ctypes.c_size_t,ctypes.c_size_t,
                          ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint32),ctypes.c_size_t,
                          ctypes.POINTER(ctypes.c_uint32),ctypes.c_uint8]
        self.fn.restype=ctypes.c_int

    def batch(self,frames,parallel=True):
        a=np.asarray(frames)
        if a.dtype!=np.uint8 or a.ndim!=3 or not 0<len(a)<=4096 or not all(0<d<=512 for d in a.shape[1:]):
            raise ValueError('Expected uint8 NxHxW frames,dimensions1..512,batch1..4096')
        a=np.ascontiguousarray(a);n,h,w=a.shape
        out=np.zeros((n,h*w,5),dtype=np.uint32);lengths=np.zeros(n,dtype=np.uint32)
        code=self.fn(a.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),a.size,h,w,n,
                     out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),out.size,
                     lengths.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),int(parallel))
        if code:raise RuntimeError(f'Rust rectangle extraction failed:{code}')
        return [[tuple(row) for row in rr[:int(k)].tolist()] for rr,k in zip(out,lengths)]

    def __call__(self,grid):return self.batch(np.asarray(grid,dtype=np.uint8)[None],parallel=False)[0]
