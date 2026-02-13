"""
security/ratelimit.py
=====================
PRODUCTION - Rate Limiting Module
"""
import streamlit as st
from collections import defaultdict
from typing import Dict, Tuple, Callable
import threading
import time
from functools import wraps

class RateLimiter:
    """Rate limiter for public endpoints"""

    def __init__(self):
        self._limits: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self._lock = threading.Lock()

        self.LIMITS = {
            'public_search_items': (100, 60),
            'public_view_items': (100, 60),
            'public_get_item_by_id': (100, 60),
            'create_item': (10, 60),
            'update_item': (10, 60),
            'delete_item': (5, 60),
            'create_user': (5, 60),
            'reset_password': (5, 60),
        }

    def is_allowed(self, action: str, session_id: str = None) -> Tuple[bool, int]:
        if session_id is None:
            session_id = st.session_state.get('session_id', 'anonymous')

        if action not in self.LIMITS:
            return True, 0

        max_requests, per_seconds = self.LIMITS[action]

        with self._lock:
            now = time.time()
            cutoff = now - per_seconds

            self._limits[session_id][action] = [
                t for t in self._limits[session_id][action] if t[0] > cutoff
            ]

            current_count = len(self._limits[session_id][action])

            if current_count >= max_requests:
                oldest = self._limits[session_id][action][0][0]
                wait_time = int(oldest + per_seconds - now)
                return False, max(1, wait_time)

            self._limits[session_id][action].append((now, current_count + 1))
            return True, 0

def rate_limit(action: str = None):
    """Decorator for rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = rate_limiter
            action_name = action or func.__name__

            allowed, wait_time = limiter.is_allowed(action_name)

            if not allowed:
                st.error(f"⚠️ คุณทำรายการถี่เกินไป กรุณารอ {wait_time} วินาที")
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator

rate_limiter = RateLimiter()