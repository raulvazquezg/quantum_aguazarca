from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile


def prepare_minus(qc: QuantumCircuit, q: int):
    # |-> = (|0> - |1>)/sqrt(2)
    qc.x(q)
    qc.h(q)


def compute_not_into(qc: QuantumCircuit, inp: int, out: int):
    """
    Compute out := NOT(inp) into a fresh |0> ancilla 'out'.
    out = 1 XOR inp
    """
    qc.x(out)
    qc.cx(inp, out)


def uncompute_not_into(qc: QuantumCircuit, inp: int, out: int):
    # Reverse of compute_not_into
    qc.cx(inp, out)
    qc.x(out)


def compute_f_from_aag(qc: QuantumCircuit, A: int, B: int, C: int,
                       n4: int, not_n4: int, not_C: int, n5: int, F: int):
    """
    Implements the AAG-shaped logic:

      n4      = A & B
      not_n4  = NOT(n4)
      not_C   = NOT(C)
      n5      = not_n4 & not_C
      F       = NOT(n5)

    All targets (n4, not_n4, not_C, n5, F) are assumed to start at |0>.
    """
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


def uncompute_f_from_aag(qc: QuantumCircuit, A: int, B: int, C: int,
                         n4: int, not_n4: int, not_C: int, n5: int, F: int):
    """
    Exact reverse of compute_f_from_aag, to clean ancillas back to |0>.
    """
    uncompute_not_into(qc, n5, F)
    qc.ccx(not_n4, not_C, n5)
    uncompute_not_into(qc, C, not_C)
    uncompute_not_into(qc, n4, not_n4)
    qc.ccx(A, B, n4)


def oracle_aag_n4_sa0(qc: QuantumCircuit,
                      A: int, B: int, C: int,
                      # good network wires
                      n4: int, not_n4: int, not_C: int, n5: int, Fg: int,
                      # faulty network wires
                      not_n4_f: int, n5_f: int, Ff: int,
                      # detect + phase
                      detect: int, phase: int):
    """
    Oracle for fault: n4 stuck-at-0 (n4 is the A&B node).

    We compute:
      - F_good via the AAG-shaped network.
      - F_faulty via an AAG-shaped network where n4 is forced to 0,
        i.e., not_n4_f is forced to 1.

    Then:
      detect = F_good XOR F_faulty
      phase kickback when detect=1
      uncompute everything
    """

    # --- Compute GOOD output Fg using the AAG shape
    compute_f_from_aag(qc, A, B, C, n4, not_n4, not_C, n5, Fg)

    # --- Compute FAULTY output Ff using the same shape but with n4 stuck at 0
    # n4_f is implicitly 0 (we don't even allocate it)
    # so not_n4_f must be 1
    qc.x(not_n4_f)                    # force not_n4_f = 1

    # not_C already computed above (shared), so:
    # n5_f = not_n4_f & not_C
    qc.ccx(not_n4_f, not_C, n5_f)

    # Ff = NOT(n5_f)
    compute_not_into(qc, n5_f, Ff)

    # --- detect = Fg XOR Ff (into 'detect' which starts at 0)
    qc.cx(Fg, detect)
    qc.cx(Ff, detect)

    # --- phase flip if detect==1
    qc.cx(detect, phase)              # X|-> = -|->

    # --- Uncompute detect
    qc.cx(Ff, detect)
    qc.cx(Fg, detect)

    # --- Uncompute FAULTY network
    uncompute_not_into(qc, n5_f, Ff)
    qc.ccx(not_n4_f, not_C, n5_f)
    qc.x(not_n4_f)                    # return not_n4_f to 0

    # --- Uncompute GOOD network (also uncomputes shared not_C)
    uncompute_f_from_aag(qc, A, B, C, n4, not_n4, not_C, n5, Fg)


def diffuser_3q(qc: QuantumCircuit, A: int, B: int, C: int):
    qc.h([A, B, C])
    qc.x([A, B, C])
    qc.h(C)
    qc.ccx(A, B, C)
    qc.h(C)
    qc.x([A, B, C])
    qc.h([A, B, C])


def main(shots=2048, iters=2):
    # Qubit indices
    A, B, C = 0, 1, 2

    # Good AAG wires
    n4      = 3
    not_n4  = 4
    not_C   = 5
    n5      = 6
    Fg      = 7

    # Faulty AAG wires (n4 stuck-at-0)
    not_n4_f = 8
    n5_f     = 9
    Ff       = 10

    # detect + phase ancilla
    detect = 11
    phase  = 12

    qc = QuantumCircuit(13, 3)

    # phase ancilla in |-> for phase kickback
    prepare_minus(qc, phase)

    # uniform superposition over input candidates
    qc.h([A, B, C])

    for _ in range(iters):
        oracle_aag_n4_sa0(
            qc, A, B, C,
            n4, not_n4, not_C, n5, Fg,
            not_n4_f, n5_f, Ff,
            detect, phase
        )
        diffuser_3q(qc, A, B, C)

    # Measure inputs; map so printed strings are ABC
    qc.measure([A, B, C], [2, 1, 0])

    sim = AerSimulator()
    tqc = transpile(qc, sim)
    result = sim.run(tqc, shots=shots).result()
    counts = result.get_counts()
    print("Counts (ABC):", counts)
    print("Top outcome:", max(counts.items(), key=lambda kv: kv[1]))

    # Save a wrapped diagram (helps with size)
    qc.draw(output="mpl", filename="figures/grover_aag_oracle.png", fold=60)

    return qc


if __name__ == "__main__":
    main()
