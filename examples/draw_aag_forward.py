from qiskit import QuantumCircuit

def compute_not_into(qc: QuantumCircuit, inp: int, out: int):
    qc.x(out)
    qc.cx(inp, out)

def build_aag_forward():
    # Qubit indices (same meaning as your oracle code)
    A, B, C = 0, 1, 2
    n4, not_n4, not_C, n5, F = 3, 4, 5, 6, 7

    qc = QuantumCircuit(8, name="AAG_forward_compute")

    # n4 = A & B
    qc.ccx(A, B, n4)

    # not_n4 = NOT(n4)
    compute_not_into(qc, n4, not_n4)

    # not_C = NOT(C)
    compute_not_into(qc, C, not_C)

    # n5 = not_n4 & not_C
    qc.ccx(not_n4, not_C, n5)

    # F = NOT(n5)
    compute_not_into(qc, n5, F)

    return qc

if __name__ == "__main__":
    qc = build_aag_forward()
    qc.draw(output="mpl", filename="figures/aag_forward_compute.png", fold=60)
    print("Wrote figures/aag_forward_compute.png")
