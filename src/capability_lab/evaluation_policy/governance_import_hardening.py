"""Install reload/reimport hardening for the PR12.7 governance surface.

The governance source intentionally contains the deterministic structural core.
Runtime authority is process-local and non-serializable. This import hook makes
that authority wrapping part of every governance module execution, including
`importlib.reload()` and removal/reimport through `sys.modules`.

A governance generation is executed in an isolated module namespace first.
Only after both authority hardeners have wrapped that isolated generation is
its namespace published onto the live import-system module. Publication is
serialized by one stable process-local lock owned by this non-reexecuted
hardening layer. Package-level readers capture the stable published generation
through that same lock, so they observe either the previous complete generation
or the replacement complete generation, never the namespace/pointer transition
between them.

The hardening layer also retains the last complete immutable generation outside
the transient `sys.modules` entry. During removal/reimport, package-level
serialization can therefore continue on the previous complete generation while
the replacement module is still initializing; once publication completes, one
locked switch makes the replacement generation current.

Governance serialization is hardened through the same import hook. Artifact
methods and classmethods resolve the immutable generation that owns their
calling function globals, while ordinary package-level serializer calls resolve
the stable currently published generation. This binds an operation at its
actual API entry even when a governance reload completes before serializer
delegation.
"""

from __future__ import annotations

import importlib
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import PathFinder
import sys
import threading
from types import ModuleType


_TARGET = "capability_lab.evaluation_policy.governance"
_SERIALIZATION_TARGET = "capability_lab.evaluation_policy.governance_serialization"
_PUBLISHED_GENERATION_ATTR = "_pr12_7_published_governance_generation"
_IMPORT_METADATA = (
    "__name__",
    "__package__",
    "__spec__",
    "__loader__",
    "__file__",
    "__cached__",
)

# `importlib.reload(governance_import_hardening)` is not a supported authority
# transition, but retaining these values across such a reload is cheap defense
# in depth. More importantly, they are stable across governance and serializer
# reload/reimport, which are explicitly supported PR12.7 boundaries.
if "_GOVERNANCE_PUBLICATION_LOCK" not in globals():
    _GOVERNANCE_PUBLICATION_LOCK = threading.RLock()
if "_CURRENT_PUBLISHED_GOVERNANCE_GENERATION" not in globals():
    _CURRENT_PUBLISHED_GOVERNANCE_GENERATION: ModuleType | None = None


def _published_generation_values(published: ModuleType) -> dict[str, object]:
    """Return the exact values used to expose one complete hardened generation."""

    return {
        name: value
        for name, value in published.__dict__.items()
        if name != _PUBLISHED_GENERATION_ATTR
    }


def reset_governance_publication_after_fork_v1() -> None:
    """Recover one complete publication state in a POSIX fork child.

    A fork may occur while another parent thread owns the publication `RLock`.
    The child inherits only the calling thread, so retaining that locked object
    could deadlock every later package-level serialization or governance
    publication in the child.

    More subtly, the fork can snapshot the live governance module after some or
    all N+1 namespace values were copied but before the stable published pointer
    advanced from N. The vanished publisher can never finish that transition in
    the child. Therefore the child re-creates the lock and, when a complete
    stable generation already exists, restores the live module to that exact
    last-complete generation before normal execution resumes.

    No import is performed here; `sys.modules` is inspected only for an already
    present live governance module. Runtime authority tables are cleared by the
    package's same `after_in_child` callback after this recovery step.
    """

    global _GOVERNANCE_PUBLICATION_LOCK
    _GOVERNANCE_PUBLICATION_LOCK = threading.RLock()

    published = _CURRENT_PUBLISHED_GOVERNANCE_GENERATION
    live = sys.modules.get(_TARGET)
    if published is None or type(live) is not ModuleType:
        return

    published = _validate_published_generation(published)
    live.__dict__.update(_published_generation_values(published))
    setattr(live, _PUBLISHED_GENERATION_ATTR, published)


def _isolated_execution_module(live_module: ModuleType) -> ModuleType:
    """Create an unregistered namespace for one source execution."""

    shadow = ModuleType(live_module.__name__)
    for name in _IMPORT_METADATA:
        if hasattr(live_module, name):
            setattr(shadow, name, getattr(live_module, name))
    return shadow


def _is_exact_origin_generation(
    candidate: object,
    caller_globals: dict[str, object],
) -> bool:
    """Accept only the shadow module that exactly owns these function globals."""

    return (
        type(candidate) is ModuleType
        and candidate.__name__ == _TARGET
        and candidate.__dict__ is caller_globals
        and caller_globals.get(_PUBLISHED_GENERATION_ATTR) is candidate
    )


def _validate_published_generation(published: object) -> ModuleType:
    """Require one exact immutable self-anchored governance generation."""

    if type(published) is not ModuleType:
        raise RuntimeError("invalid PR12.7 published governance generation")
    if (
        published.__name__ != _TARGET
        or published.__dict__.get(_PUBLISHED_GENERATION_ATTR) is not published
    ):
        raise RuntimeError("untrusted PR12.7 published governance generation")
    return published


def _stable_current_published_generation() -> ModuleType:
    """Capture the current complete generation without consulting `sys.modules`.

    A replacement import inserts an initializing live module into `sys.modules`
    before its loader has produced a complete hardened generation. The stable
    pointer here deliberately remains on the previous complete generation until
    final publication. On the very first import, when no previous generation
    exists, importing the target through the normal import machinery waits for
    any concurrent initialization to finish before this function retries.
    """

    with _GOVERNANCE_PUBLICATION_LOCK:
        published = _CURRENT_PUBLISHED_GOVERNANCE_GENERATION
    if published is not None:
        return _validate_published_generation(published)

    # First-publication fallback only. Do not short-circuit through
    # `sys.modules.get`: `import_module` participates in Python's import-lock
    # protocol and therefore waits for a concurrent initializing target.
    importlib.import_module(_TARGET)
    with _GOVERNANCE_PUBLICATION_LOCK:
        published = _CURRENT_PUBLISHED_GOVERNANCE_GENERATION
    if published is None:
        raise RuntimeError("missing PR12.7 published governance generation")
    return _validate_published_generation(published)


def _serialization_operation_governance() -> ModuleType:
    """Resolve one immutable governance generation at the real API entry.

    `governance_serialization` calls this helper from inside one of its public
    serializer functions. Two frames above this helper is therefore the caller
    of that public function. If that caller is a governance artifact method or
    classmethod, its function globals belong to the immutable shadow generation
    that defined the artifact class. Otherwise this is an ordinary package-level
    serializer call and the stable current published generation is the correct
    basis.

    A same-named global is not sufficient: the candidate generation must be the
    exact ModuleType whose `__dict__` is the caller's function globals. This
    prevents unrelated caller modules from accidentally or deliberately changing
    package-level serializer generation selection by defining the internal
    pointer name themselves.
    """

    try:
        caller_globals = sys._getframe(2).f_globals
    except (ValueError, AttributeError):
        caller_globals = {}
    originating_generation = caller_globals.get(_PUBLISHED_GENERATION_ATTR)
    if _is_exact_origin_generation(originating_generation, caller_globals):
        return originating_generation

    return _stable_current_published_generation()


def _publish_live_namespace_values(
    module: ModuleType,
    published_values: dict[str, object],
) -> None:
    """Publish already-hardened values while the stable publication lock is held."""

    module.__dict__.update(published_values)


class _GovernanceHardeningLoader(Loader):
    def __init__(self, delegate: Loader) -> None:
        self._delegate = delegate

    def create_module(self, spec):
        create_module = getattr(self._delegate, "create_module", None)
        if create_module is None:
            return None
        return create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        global _CURRENT_PUBLISHED_GOVERNANCE_GENERATION

        # Never execute the structural governance source into the live module.
        # During reload that live object can be retained and read concurrently.
        # Executing into a detached namespace keeps the previous hardened
        # generation authoritative until the replacement generation is itself
        # fully hardened.
        shadow = _isolated_execution_module(module)
        self._delegate.exec_module(shadow)

        # These stable authority modules deliberately do not import governance.
        # They wrap the isolated generation before any of its definitions are
        # published through the live target module.
        from .review_process_authority import harden_governance_review_authority
        from .registry_authority import harden_governance_registry_authority

        harden_governance_review_authority(shadow)
        harden_governance_registry_authority(shadow)

        # Functions/classes defined in this shadow retain this dictionary as
        # their globals forever. Give those artifact methods a direct immutable
        # self-generation anchor before publication.
        setattr(shadow, _PUBLISHED_GENERATION_ATTR, shadow)
        published_values = _published_generation_values(shadow)

        # One publication critical section covers all three externally relevant
        # views: live attributes, the live compatibility pointer, and the stable
        # package-level generation pointer. Package-level serializer selection
        # takes this same lock. Therefore a reader that encounters newly exposed
        # N+1 live classes during this update cannot select stale N: it waits for
        # the critical section and then captures complete N+1. Before the section
        # begins, readers continue to use complete N.
        with _GOVERNANCE_PUBLICATION_LOCK:
            _publish_live_namespace_values(module, published_values)
            setattr(module, _PUBLISHED_GENERATION_ATTR, shadow)
            _CURRENT_PUBLISHED_GOVERNANCE_GENERATION = shadow

    def __getattr__(self, name: str):
        return getattr(self._delegate, name)


class _GovernanceSerializationHardeningLoader(Loader):
    """Publish serializer source only after binding origin-aware generation lookup."""

    def __init__(self, delegate: Loader) -> None:
        self._delegate = delegate

    def create_module(self, spec):
        create_module = getattr(self._delegate, "create_module", None)
        if create_module is None:
            return None
        return create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        # Serializer reload is isolated too, so a retained serializer module
        # never exposes its source-defined current-generation lookup before this
        # stronger origin-aware helper is installed.
        shadow = _isolated_execution_module(module)
        self._delegate.exec_module(shadow)
        shadow._governance = _serialization_operation_governance
        module.__dict__.update(shadow.__dict__)

    def __getattr__(self, name: str):
        return getattr(self._delegate, name)


class _GovernanceHardeningFinder(MetaPathFinder):
    _capability_lab_governance_hardening_finder = True

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname not in {_TARGET, _SERIALIZATION_TARGET}:
            return None
        spec = PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None:
            return spec
        if fullname == _TARGET:
            if isinstance(spec.loader, _GovernanceHardeningLoader):
                return spec
            spec.loader = _GovernanceHardeningLoader(spec.loader)
            return spec
        if isinstance(spec.loader, _GovernanceSerializationHardeningLoader):
            return spec
        spec.loader = _GovernanceSerializationHardeningLoader(spec.loader)
        return spec


def install_governance_import_hardening_v1() -> None:
    """Install exactly one narrow finder for governance and its serializer."""

    for finder in sys.meta_path:
        if getattr(
            finder,
            "_capability_lab_governance_hardening_finder",
            False,
        ):
            return
    sys.meta_path.insert(0, _GovernanceHardeningFinder())
