from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class InventoryError(RuntimeError):
    """Raised when Phase 0 cannot produce a trustworthy inventory."""


@dataclass(frozen=True, slots=True)
class SourceState:
    root: Path
    branch: str
    head_sha: str
    dirty: bool
    remotes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["root"] = str(self.root)
        return data
