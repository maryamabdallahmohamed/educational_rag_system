"""Thread-safe singleton utilities."""
from threading import Lock
from typing import Any, Dict, Type

class SingletonMeta(type):
    """Metaclass implementing a thread-safe singleton."""

    _instances: Dict[Type[Any], Any] = {}
    _locks: Dict[Type[Any], Lock] = {}

    def __call__(cls, *args, **kwargs):  # type: ignore[override]
        if cls not in cls._instances:
            cls._locks.setdefault(cls, Lock())
            with cls._locks[cls]:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]

    @classmethod
    def reset_instance(mcs, target_cls: Type[Any]) -> None:
        """Clear cached singleton instance (mainly for tests)."""
        if target_cls in mcs._instances:
            mcs._locks.setdefault(target_cls, Lock())
            with mcs._locks[target_cls]:
                instance = mcs._instances.pop(target_cls, None)
                if instance is not None and hasattr(instance, "_initialized"):
                    setattr(instance, "_initialized", False)


def reset_singleton(target_cls: Type[Any]) -> None:
    """Helper to reset singleton instance cache."""
    SingletonMeta.reset_instance(target_cls)
