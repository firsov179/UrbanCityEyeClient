"""
Logging utilities for consistent output across the application
"""
import js


def log(msg="", *args, level="info"):
    """
    Log messages to console in a consistent way.
    Will log to JavaScript console if available, otherwise to Python console.

    Args:
        msg: Primary message to log (can be empty)
        *args: Additional messages
        level: Log level (info, warn, error)
    """
    if args:
        message = " ".join([str(msg)] + [str(arg) for arg in args])
    else:
        message = str(msg)

    try:
        import js
        if level == "error":
            js.console.error(message)
        elif level == "warn":
            js.console.warn(message)
        else:
            js.console.log(message)
    except ImportError:
        pass


def error(*args):
    """Log error message"""
    log(*args, level="error")


def warn(*args):
    """Log warning message"""
    log(*args, level="warn")
