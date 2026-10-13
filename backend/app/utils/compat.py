"""
Compatibility utilities for Python version transitions and PEP 810 Lazy Imports.
Provides zero-overhead runtime stubs on Python < 3.15 (e.g. Python 3.11)
and native PEP 810 __lazy_modules__ registration on Python >= 3.15.
"""

import sys
from typing import Any

IS_PYTHON_315_PLUS = sys.version_info >= (3, 15)
IS_PYTHON_312_PLUS = sys.version_info >= (3, 12)


def declare_lazy(*module_names: str) -> None:
    """
    Registers module names to be lazily imported.
    
    On Python 3.15+ with PEP 810, this injects the module names into the caller's
    module-level `__lazy_modules__` list, instructing the interpreter to defer
    loading until first attribute access.
    
    On Python < 3.15 (e.g., Python 3.11), this is a transparent no-op so normal
    eager imports proceed without errors or syntax issues.
    """
    if IS_PYTHON_315_PLUS:
        frame = sys._getframe(1)
        existing = frame.f_globals.setdefault("__lazy_modules__", [])
        for name in module_names:
            if name not in existing:
                existing.append(name)


class LazyModuleProxy:
    """
    A lightweight fallback proxy for Python < 3.15 that delays importing
    heavy modules (such as torch, xgboost, sklearn) until an attribute is accessed.
    """

    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module: Any = None

    def _load(self) -> Any:
        if self._module is None:
            import importlib
            self._module = importlib.import_module(self._module_name)
        return self._module

    def __getattr__(self, name: str) -> Any:
        module = self._load()
        return getattr(module, name)

    def __repr__(self) -> str:
        if self._module is None:
            return f"<LazyModuleProxy for '{self._module_name}' (unloaded)>"
        return repr(self._module)


def lazy_import(module_name: str) -> Any:
    """
    Returns a lazy proxy object for a module on Python < 3.15,
    or directly imports when running on Python 3.15+ with declare_lazy.
    """
    if IS_PYTHON_315_PLUS:
        import importlib
        return importlib.import_module(module_name)
    return LazyModuleProxy(module_name)
