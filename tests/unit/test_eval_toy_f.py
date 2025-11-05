import pytest
from aguazarca.blocks.a_frontend.ir.model import CircuitIR, Node, GateType
from aguazarca.blocks.a_frontend.ir.eval import eval_vec

@pytest.fixture
def toy_ir():
    # F = (A & B) | C
    nodes = [
        Node("A", GateType.PI, []),
        Node("B", GateType.PI, []),
        Node("C", GateType.PI, []),
        Node("D", GateType.AND, ["A", "B"]),
        Node("F", GateType.OR,  ["D", "C"]),
        Node("F_PO", GateType.PO, ["F"]),
    ]
    return CircuitIR(
        name="toy_direct",
        primary_inputs=["A", "B", "C"],
        primary_outputs=["F_PO"],
        nodes=nodes,
    )

@pytest.mark.toy
@pytest.mark.parametrize(
    "A,B,C,expect",
    [
        (1,1,0,1),  # A&B=1, C=0 -> F=1
        (0,0,1,1),  # A&B=0, C=1 -> F=1
        (1,0,0,0),  # A&B=0, C=0 -> F=0
    ],
)
def test_eval_toy_f(toy_ir, A, B, C, expect):
    out = eval_vec(toy_ir, {"A": A, "B": B, "C": C})
    assert out["F_PO"] == expect
