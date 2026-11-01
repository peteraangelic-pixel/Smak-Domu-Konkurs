"""Prototype: re-observing the current board clears only the stale-belief latch.

No automatic action, no change to known-noop/death/repeated-state/terminal guards.
Merely reading a board is not proof that the model's interpretation is right.
"""


def install(sandbox):
    if getattr(sandbox,'_fresh_state_read_installed',False):return
    source=sandbox._SANDBOX_BOOTSTRAP
    anchor='    _stale_state: list[str] = []'
    assert source.count(anchor)==1
    source=source.replace(anchor,anchor+'''
    _user_frame_reads = [True]
    _original_frame_getattribute = FrameView.__getattribute__
    def _observed_frame_getattribute(self, name):
        value = _original_frame_getattribute(self, name)
        if (name in ('ascii', 'segmentation') and _user_frame_reads[0]
                and _stale_state and self is runtime_globals.get('current_frame')):
            del _stale_state[:]
            stdout.write('FRESH_STATE_READ reobserved=1\\n')
        return value
    FrameView.__getattribute__ = _observed_frame_getattribute
''')
    anchor='    runtime_globals["action"] = action'
    assert source.count(anchor)==1
    source=source.replace(anchor,'''    _unobserved_action = action
    def _fresh_read_action(actions):
        # Frame refreshes and diagnostics inside action() are not user reads.
        _user_frame_reads[0] = False
        try:
            return _unobserved_action(actions)
        finally:
            _user_frame_reads[0] = True
    runtime_globals["action"] = _fresh_read_action''')
    compile(source,'<fresh-state-read-bootstrap>','exec')
    sandbox._SANDBOX_BOOTSTRAP=source
    sandbox._fresh_state_read_installed=True
