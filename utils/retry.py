"""
Retry logic with exponential backoff
"""
import time
import random
from typing import Callable, Any
from functools import wraps


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be exponentially increased)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(delay)
                    else:
                        # Last attempt failed
                        raise last_exception

        return wrapper
    return decorator