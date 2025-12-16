from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Tuple


class FaultType(str, Enum):
    SA0 = "sa0"
    SA1 = "sa1"

    @property
    def stuck_value(self) -> int:
        return 0 if self == FaultType.SA0 else 1


@dataclass(frozen=True)
class FaultSite:
    """
    Fault site on the CircuitIR, identified by the *net name* (Node.name).
    kind is for display/debug: PI/AND/PO/...
    """
    net: str
    kind: str


@dataclass(frozen=True)
class Cone:
    """
    Fan-out cone starting at a fault site net:
      - nets: all downstream nets reachable (including the site net itself)
      - outputs: which primary outputs depend on this site
    """
    nets: FrozenSet[str]
    outputs: Tuple[str, ...]


@dataclass(frozen=True)
class Fault:
    site: FaultSite
    ftype: FaultType
    cone: Cone

    @property
    def id_str(self) -> str:
        return f"{self.site.net}:{self.ftype.value}"
