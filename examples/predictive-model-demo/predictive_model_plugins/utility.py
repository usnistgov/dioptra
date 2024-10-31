from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union


def ensure_list(string: List | str) -> List:
    """Utility: coerces a string into a list."""
    if isinstance(string, str):
        return [string]
    elif isinstance(string, list):
        return string
    else:
        raise ValueError
