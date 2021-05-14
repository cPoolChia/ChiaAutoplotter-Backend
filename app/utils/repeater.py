from typing import Optional, Callable, Any
import logging
import time


def repeats(
    amount: int,
    *,
    delay: float = 1,
    message: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable], Callable]:
    if message is not None and logger is None:
        raise ValueError("To print message also specify a logger to use")
    if amount < 1:
        raise ValueError(f"Amount should be > 0, got {amount}")

    def decorator(f: Callable) -> Callable:
        def wrapped(*args: list[Any], **kwargs: dict[Any, Any]) -> Any:
            error_args = []
            for i in range(amount):
                try:
                    return f(*args, **kwargs)
                except Exception as ex:
                    if message and logger:
                        logger.exception(
                            f"[{i+1}/{amount}] {message}. [{ex.__class__.__name__} | {ex.args}]"
                        )
                    error_args.append(ex.args)
                    time.sleep(delay)
            raise RuntimeError(*error_args)

        return wrapped

    return decorator
