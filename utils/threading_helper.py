"""
Helpers pour gérer les threads GUI de manière safe
"""

import threading
from typing import Callable, Any
import traceback


def run_in_thread(func: Callable, on_success: Callable = None, on_error: Callable = None, *args, **kwargs):
    """
    Exécute une fonction dans un thread séparé
    
    Args:
        func: Fonction à exécuter
        on_success: Callback appelé en cas de succès (avec le résultat)
        on_error: Callback appelé en cas d'erreur (avec l'exception)
        *args, **kwargs: Arguments pour func
    """
    def wrapper():
        try:
            result = func(*args, **kwargs)
            if on_success:
                on_success(result)
        except Exception as e:
            if on_error:
                on_error(e)
            else:
                print(f"Thread error: {e}")
                traceback.print_exc()
    
    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    return thread


class ThreadSafeLogger:
    """
    Logger thread-safe pour GUI Tkinter
    """
    
    def __init__(self, log_func: Callable):
        """
        Args:
            log_func: Fonction de log (ex: widget.log)
        """
        self.log_func = log_func
    
    def log(self, message: str):
        """Log un message de manière thread-safe"""
        try:
            self.log_func(message)
        except Exception as e:
            print(f"Log error: {e}")
            print(f"Message was: {message}")
