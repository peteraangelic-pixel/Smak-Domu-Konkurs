# r077 · push

STATUS=FAILED (UTC 2026-10-25 12:40:28)

BŁĄD: push dozwolony tylko pod /home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle; dostalem /home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/duck-v9

TRACEBACK:
Traceback (most recent call last):
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 558, in main
    text = OPS[op_name](args, out_dir)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 157, in op_push
    pkg = _safe_pkg_dir(str(args.get("dir") or ""))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 150, in _safe_pkg_dir
    raise ValueError(f"push dozwolony tylko pod {root}; dostalem {candidate}")
ValueError: push dozwolony tylko pod /home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle; dostalem /home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/duck-v9

