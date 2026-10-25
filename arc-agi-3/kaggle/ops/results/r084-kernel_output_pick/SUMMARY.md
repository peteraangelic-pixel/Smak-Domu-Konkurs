# r084 · kernel_output_pick

STATUS=FAILED (UTC 2026-10-25 15:00:18)

BŁĄD: HTTP Error 400: Bad Request

TRACEBACK:
Traceback (most recent call last):
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 598, in main
    text = OPS[op_name](args, out_dir)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 198, in op_kernel_output_pick
    with urllib.request.urlopen(req, timeout=1800) as r, open(tmp_zip, "wb") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/urllib/request.py", line 215, in urlopen
    return opener.open(url, data, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/urllib/request.py", line 521, in open
    response = meth(req, response)
               ^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/urllib/request.py", line 630, in http_response
    response = self.parent.error(
               ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/urllib/request.py", line 559, in error
    return self._call_chain(*args)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/urllib/request.py", line 492, in _call_chain
    result = func(*args)
             ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.15/x64/lib/python3.12/urllib/request.py", line 639, in http_error_default
    raise HTTPError(req.full_url, code, msg, hdrs, fp)
urllib.error.HTTPError: HTTP Error 400: Bad Request

