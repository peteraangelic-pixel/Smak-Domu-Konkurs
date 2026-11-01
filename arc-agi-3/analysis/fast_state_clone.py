"""Independent full-state clone via C pickle, never sharing mutable templates.

Offline evaluator only. Dynamic environment modules must be registered in
sys.modules by the loader. No modification of global copy/pickle dispatch.
"""
import copyreg
import io
import pickle
from arcengine import GameAction


class StatePickler(pickle.Pickler):
    dispatch_table=copyreg.dispatch_table.copy()
    # arcengine overrides Enum._value_ after construction; ordinary unpickling
    # calls GameAction(0), which fails. Restore the existing enum by its name.
    dispatch_table[GameAction]=lambda action:(getattr,(GameAction,action.name))


def dumps(state):
    stream=io.BytesIO()
    StatePickler(stream,protocol=5).dump(state)
    return stream.getvalue()


def clone(state):
    return pickle.loads(dumps(state))
