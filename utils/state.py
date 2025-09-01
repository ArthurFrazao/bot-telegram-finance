from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class UserState:
    step: str = ""
    buffer: Dict[str, Any] = field(default_factory=dict)
    last_message_id: int | None = None

STATE: Dict[int, UserState] = {}

def set_state(user_id: int, step: str, **kw):
    st = STATE.get(user_id, UserState())
    st.step = step
    for k, v in kw.items():
        setattr(st, k, v)
    STATE[user_id] = st
    return st

def get_state(user_id: int) -> UserState:
    return STATE.get(user_id, UserState())

def clear_state(user_id: int):
    STATE.pop(user_id, None)