from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

class GateType(Enum):
    PI = "PI"
    PO = "PO"
    AND = "AND"
    OR  = "OR"
    NOT = "NOT"
    BUF = "BUF"
    CONST = "CONST"  # const-0/1

@dataclass
class Node:
    name: str                 # unique net name
    type: GateType
    inputs: List[str] = field(default_factory=list)
    attrs: Dict[str, str] = field(default_factory=dict)

@dataclass
class CircuitIR:
    name: str
    primary_inputs: List[str]
    primary_outputs: List[str]
    nodes: List[Node]
