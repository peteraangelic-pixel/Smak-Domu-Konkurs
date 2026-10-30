"""Direct ctypes FFI to the local Rust cdylib. Fail loudly if unavailable."""
import ctypes
from pathlib import Path
import sys
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def native_kernels():
    return NativeKernels()


class NativeKernels:
    def __init__(self):
        filename = 'arc3.dll' if sys.platform == 'win32' else ('libarc3.dylib' if sys.platform == 'darwin' else 'libarc3.so')
        path = Path(__file__).resolve().parents[1] / 'rust/target/release' / filename
        self.library = ctypes.CDLL(str(path))
        self.function = self.library.arc3_blob_batch
        byte_pointer = ctypes.POINTER(ctypes.c_uint8)
        int_pointer = ctypes.POINTER(ctypes.c_uint32)
        size = ctypes.c_size_t
        self.function.argtypes = [byte_pointer, size, size, size, size, size, int_pointer, size, int_pointer, ctypes.c_uint8]
        self.function.restype = ctypes.c_int
        self.backend = 'rust-ctypes'

    def blob_batch(self, frames, limit=28, parallel=True):
        array = np.asarray(frames)
        if array.ndim != 3 or not 0 < array.shape[1] <= 512 or not 0 < array.shape[2] <= 512 or array.shape[0] > 4096:
            raise ValueError('Expected up to 4096 frames with shape H x W, dimensions 1..512')
        if not isinstance(limit, int) or limit < 0 or limit > array.shape[1] * array.shape[2]:
            raise ValueError('Invalid click limit')
        if limit == 0:
            return [[] for _ in array]
        if array.dtype != np.uint8:
            raise ValueError('Frames must have uint8 dtype')
        array = np.ascontiguousarray(array)
        count, height, width = array.shape
        output = np.zeros((count, limit, 2), dtype=np.uint32)
        lengths = np.zeros(count, dtype=np.uint32)
        status = self.function(
            array.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), array.size,
            height, width, count, limit,
            output.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)), output.size,
            lengths.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)), int(parallel))
        if status:
            raise RuntimeError(f'Rust blob kernel failed with status {status}')
        return [[tuple(map(int, point)) for point in row[:length]] for row, length in zip(output, lengths)]

    def blob_candidates(self, frame, limit=28):
        # Search workers already run in separate processes. Single-frame calls
        # remain serial inside Rust, avoiding nested Rayon pools.
        return self.blob_batch(np.asarray(frame)[None], limit, parallel=False)[0]
