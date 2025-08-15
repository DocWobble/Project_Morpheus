"""Utilities for working with the :mod:`orpheus_cpp` engine locally.

This module provides helpers for constructing :class:`orpheus_cpp.OrpheusCpp`
instances while allowing a custom SNAC decoder session to be supplied.  The
current release of ``orpheus-cpp`` does not expose a public parameter or method
to override the internal ONNX session, so we fall back to assigning to the
private ``_snac_session`` attribute.  The assignment is wrapped in
:func:`inject_snac_session` which performs version checks and emits descriptive
error messages to avoid silent breakage should the upstream package change.
"""

from __future__ import annotations

from importlib import metadata
from typing import Any, Optional
import inspect

try:  # pragma: no cover - import error handled at runtime
    import orpheus_cpp
except ImportError as exc:  # pragma: no cover - thin wrapper around ImportError
    raise RuntimeError(
        "The 'orpheus-cpp' package is required for the local Orpheus engine"
    ) from exc


def inject_snac_session(engine: Any, session: Any) -> None:
    """Inject ``session`` into ``engine``'s SNAC decoder.

    Parameters
    ----------
    engine:
        Instance of :class:`orpheus_cpp.OrpheusCpp` whose decoder session should
        be replaced.
    session:
        ONNX ``InferenceSession`` compatible object.

    This helper guards the private attribute assignment with a version check so
    callers receive a clear message if a newer ``orpheus-cpp`` release changes
    its internals.
    """

    try:
        version = metadata.version("orpheus-cpp")
    except metadata.PackageNotFoundError:  # pragma: no cover - metadata lookup
        version = "unknown"

    if not hasattr(engine, "_snac_session"):
        raise RuntimeError(
            "orpheus-cpp %s does not expose a '_snac_session' attribute; "
            "cannot inject a custom SNAC session." % version
        )

    engine._snac_session = session  # type: ignore[attr-defined]


def create_orpheus(
    *, snac_session: Optional[Any] = None, **kwargs: Any
) -> "orpheus_cpp.OrpheusCpp":
    """Create an :class:`orpheus_cpp.OrpheusCpp` instance.

    If ``snac_session`` is provided and the current version of ``orpheus-cpp``
    exposes a public constructor argument for it, that parameter is used.  When
    such an argument is absent, :func:`inject_snac_session` is used to assign to
    the private attribute instead.
    """

    init_params = inspect.signature(orpheus_cpp.OrpheusCpp).parameters
    if snac_session is not None and "snac_session" in init_params:
        return orpheus_cpp.OrpheusCpp(snac_session=snac_session, **kwargs)

    engine = orpheus_cpp.OrpheusCpp(**kwargs)
    if snac_session is not None:
        inject_snac_session(engine, snac_session)
    return engine
