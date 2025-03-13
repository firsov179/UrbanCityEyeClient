"""
Logging utilities for consistent output across the application
"""
import sys

# Сохраняем глобальную ссылку на js для использования в функции log
try:
    import js as js_global
except ImportError:
    js_global = None

def log(*args, level="info"):
    """
    Log messages to console in a consistent way.
    Will log to JavaScript console if available, otherwise to Python console.

    Args:
        *args: Messages to log
        level: Log level (info, warn, error)
    """
    # Convert all arguments to strings and join with space
    message = " ".join(str(arg) for arg in args)

    # Log to Python console
    print(message)

    # Log to JavaScript console if available
    if js_global:
        if level == "error":
            js_global.console.error(message)
        elif level == "warn":
            js_global.console.warn(message)
        else:
            js_global.console.log(message)

def error(*args):
    """Log error message"""
    log(*args, level="error")

def warn(*args):
    """Log warning message"""
    log(*args, level="warn")
