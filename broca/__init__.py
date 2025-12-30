"""Broca package init shim
Expose optional process_single_task if an adapter is present under benchmarks.procedural_emergence
"""
__all__ = []

# Try to import an adapter (non-fatal)
try:
    from benchmarks.procedural_emergence.broca_adapter import process_single_task
    # Expose at package level for convenience
    globals()['process_single_task'] = process_single_task
    __all__.append('process_single_task')
except Exception:
    # Adapter not present or import failed — leave package minimal
    pass
