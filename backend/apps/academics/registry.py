"""The curriculum plugin registry — docs/modules.md's Layer 2 inversion:
nothing here ever imports a `curriculum_*` app. Each curriculum app
registers itself via its own `AppConfig.ready()` instead
(`apps/curriculum_cbc/apps.py` is the reference), so this module has zero
knowledge of which curricula exist — adding a 6th curriculum needs no
change here at all, not even a settings edit.
"""

_registry: dict[str, type] = {}


def register(curriculum_type: str, engine_class: type) -> None:
    """Called from a curriculum_* app's `AppConfig.ready()`. Stores the
    class itself, not an instance — `resolve()` instantiates fresh on
    every call, since engines are stateless (same reasoning every other
    app in this project keeps writes/reads as plain functions rather than
    objects with state)."""
    _registry[curriculum_type] = engine_class


def resolve(curriculum_type: str):
    """Instantiating an incomplete `AssessmentEngine`/`ReportEngine`
    subclass raises `TypeError` here via Python's own ABC machinery —
    that's the registry's entire "plugin validation" story; no separate
    check is needed."""
    try:
        engine_class = _registry[curriculum_type]
    except KeyError:
        raise ValueError(f"No curriculum plugin registered for {curriculum_type!r}.") from None
    return engine_class()
