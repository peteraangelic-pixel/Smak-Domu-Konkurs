"""Experimental bootstrap patch: explain unsupported TransitionView.step.

No attribute is fabricated, no action retried, and AttributeError still raises.
Not yet a packaged or quality-tested competition candidate.
"""

ANCHOR = '''            self.result = dict(result) if isinstance(result, dict) else {}

        def __str__(self):
            return (
                "ActionTransitionView("'''

REPLACEMENT = '''            self.result = dict(result) if isinstance(result, dict) else {}

        def __getattr__(self, name):
            if name == "step":
                raise AttributeError(
                    "TRANSITION_SCHEMA: TransitionView has no step attribute. "
                    "Use before_frame.step or after_frame.step for the corresponding "
                    "frame index; frame aliases after_frame. Supported transition "
                    "fields: action, before_frame, after_frame, frame, result. "
                    "Choose the before/after frame required by your comparison.")
            raise AttributeError("TransitionView has no attribute %r" % name)

        def __str__(self):
            return (
                "ActionTransitionView("'''


def patch_bootstrap(source):
    if 'TRANSITION_SCHEMA:' in source:
        return source
    if source.count(ANCHOR) != 1:
        raise ValueError('Expected exactly one TransitionView schema anchor')
    return source.replace(ANCHOR, REPLACEMENT)
