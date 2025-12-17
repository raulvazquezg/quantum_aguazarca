from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Tuple

from aguazarca.blocks.a_frontend.ir.model import CircuitIR, Node, GateType
from aguazarca.blocks.a_frontend.ir.dag import toposort
from aguazarca.blocks.a_frontend.ir.eval import eval_vec  # good evaluator


@dataclass(frozen=True)
class DetectionResult:
    vec: Dict[str, int]
    good_outs: Dict[str, int]
    faulty_outs: Dict[str, int]
    detected: bool
    diffs: Dict[str, Tuple[int, int]]  # po -> (good, faulty)


def eval_vec_faulty(ir: CircuitIR, vec: Dict[str, int], fault_net: str, stuck: int) -> Dict[str, int]:
    """
    Evaluate circuit with a single stuck-at fault on net 'fault_net'.

    Semantics (simple + correct for stuck-at):
      - If the current node name == fault_net, force its value to stuck (0/1)
        regardless of its gate type and fanins.
      - Nodes downstream will naturally consume the stuck value.
    """
    stuck = 1 if int(stuck) else 0
    values: Dict[str, int] = {k: 1 if int(v) else 0 for k, v in vec.items()}
    nodes_by_name: Dict[str, Node] = {n.name: n for n in ir.nodes}
    order: List[str] = toposort(ir)

    def bit(x: int) -> int:
        return 1 if x else 0

    for name in order:
        # Fault injection: override this net
        if name == fault_net:
            values[name] = stuck
            continue

        n = nodes_by_name[name]
        t = n.type

        if t == GateType.PI:
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
            src = n.inputs[0]
            values[name] = values[src]

        else:
            raise NotImplementedError(f"Gate type {t} not supported in faulty evaluator.")

    return {po: values[po] for po in ir.primary_outputs}


def compare_good_vs_faulty(
    ir: CircuitIR,
    vec: Dict[str, int],
    fault_net: str,
    stuck: int,
) -> DetectionResult:
    good = eval_vec(ir, vec)
    faulty = eval_vec_faulty(ir, vec, fault_net=fault_net, stuck=stuck)

    diffs: Dict[str, Tuple[int, int]] = {}
    for po in ir.primary_outputs:
        if good[po] != faulty[po]:
            diffs[po] = (good[po], faulty[po])

    return DetectionResult(
        vec={k: 1 if int(v) else 0 for k, v in vec.items()},
        good_outs=good,
        faulty_outs=faulty,
        detected=len(diffs) > 0,
        diffs=diffs,
    )


def iter_all_input_vecs(ir: CircuitIR) -> List[Dict[str, int]]:
    """
    Exhaustively enumerate all PI vectors (2^n) in a stable PI order.
    """
    pis = list(ir.primary_inputs)
    all_vecs: List[Dict[str, int]] = []
    for bits in product([0, 1], repeat=len(pis)):
        all_vecs.append({pis[i]: int(bits[i]) for i in range(len(pis))})
    return all_vecs


def find_detecting_vectors(
    ir: CircuitIR,
    fault_net: str,
    stuck: int,
) -> List[DetectionResult]:
    """
    Exhaustively find all vectors that detect the fault (for small PI count).
    """
    results: List[DetectionResult] = []
    for vec in iter_all_input_vecs(ir):
        r = compare_good_vs_faulty(ir, vec, fault_net=fault_net, stuck=stuck)
        if r.detected:
            results.append(r)
    return results
