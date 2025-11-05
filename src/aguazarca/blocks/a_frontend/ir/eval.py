from __future__ import annotations
from typing import Dict, List
from aguazarca.blocks.a_frontend.ir.model import CircuitIR, Node, GateType
from aguazarca.blocks.a_frontend.ir.dag import toposort
import json

def eval_vec(ir: CircuitIR, vec: Dict[str, int]) -> Dict[str, int]:
    """
    Evaluate the circuit for a given primary input assignment.
    Returns a dict of primary_outputs -> bit (0/1).
    Works on our IR (which may contain PI, PO, AND, OR, NOT, BUF, CONST).
    """
    # normalize input bits to {0,1}
    values: Dict[str, int] = {k: 1 if int(v) else 0 for k, v in vec.items()}
    nodes_by_name: Dict[str, Node] = {n.name: n for n in ir.nodes}
    order: List[str] = toposort(ir)

    def bit(x: int) -> int:  # defensive, ensure 0/1
        return 1 if x else 0

    for name in order:
        n = nodes_by_name[name]
        t = n.type

        if t == GateType.PI:
            # Keep provided value; default to 0 if missing
            values.setdefault(name, 0)

        elif t == GateType.CONST:
            values[name] = 1 if n.attrs.get("value", "0") == "1" else 0

        elif t == GateType.BUF:
            if n.inputs:
                values[name] = values[n.inputs[0]]

        elif t == GateType.NOT:
            values[name] = 1 - values[n.inputs[0]]

        elif t == GateType.AND:
            a, b = values[n.inputs[0]], values[n.inputs[1]]
            values[name] = bit(a & b)

        elif t == GateType.OR:
            a, b = values[n.inputs[0]], values[n.inputs[1]]
            values[name] = bit(a | b)

        elif t == GateType.PO:
            # POs are just views of their single driver
            src = n.inputs[0]
            values[name] = values[src]

        else:
            raise NotImplementedError(f"Gate type {t} not supported in evaluator.")

    return {po: values[po] for po in ir.primary_outputs}


# Convenience: load IR from a JSON file written by your CLI
def load_ir_json(path: str) -> CircuitIR:
    from .model import CircuitIR, Node, GateType
    data = json.load(open(path))
    nodes = [
        Node(n["name"], GateType(n["type"]), n.get("inputs", []), n.get("attrs", {}))
        for n in data["nodes"]
    ]
    return CircuitIR(
        name=data["name"],
        primary_inputs=data["primary_inputs"],
        primary_outputs=data["primary_outputs"],
        nodes=nodes,
    )
