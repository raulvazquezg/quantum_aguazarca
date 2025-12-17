from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit import transpile

import matplotlib.pyplot as plt


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
    qc.ccx(A, B, n4)
    compute_not_into(qc, n4, not_n4)
    compute_not_into(qc, C, not_C)
    qc.ccx(not_n4, not_C, n5)
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
    # GOOD output
    compute_f_from_aag(qc, A, B, C, n4, not_n4, not_C, n5, Fg)

    # FAULTY output: n4 stuck-at-0 => not_n4_f = 1
    qc.x(not_n4_f)
    qc.ccx(not_n4_f, not_C, n5_f)
    compute_not_into(qc, n5_f, Ff)

    # detect = Fg XOR Ff
    qc.cx(Fg, detect)
    qc.cx(Ff, detect)

    # phase flip if detect==1 (phase ancilla is |->)
    qc.cx(detect, phase)

    # Uncompute detect
    qc.cx(Ff, detect)
    qc.cx(Fg, detect)

    # Uncompute faulty network
    uncompute_not_into(qc, n5_f, Ff)
    qc.ccx(not_n4_f, not_C, n5_f)
    qc.x(not_n4_f)

    # Uncompute good network
    uncompute_f_from_aag(qc, A, B, C, n4, not_n4, not_C, n5, Fg)


def diffuser_3q(qc: QuantumCircuit, A: int, B: int, C: int):
    qc.h([A, B, C])
    qc.x([A, B, C])
    qc.h(C)
    qc.ccx(A, B, C)
    qc.h(C)
    qc.x([A, B, C])
    qc.h([A, B, C])


def plot_counts_bar(counts: dict, shots: int, title: str, out_png: str):
    # Show all 8 outcomes in ABC order
    outcomes = [f"{i:03b}" for i in range(8)]
    values = [counts.get(o, 0) for o in outcomes]

    plt.figure()
    plt.bar(outcomes, values)
    plt.xlabel("Outcome (ABC)")
    plt.ylabel(f"Counts out of {shots} shots")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.show()


def main(shots=2048, iters=1):
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

    # (Oracle convention) phase ancilla in |-> for phase kickback
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

    # Save circuit diagram
    qc.draw(output="mpl", filename="figures/grover_aag_oracle.png", fold=60)

    # NEW: plot bar chart + save PNG
    plot_counts_bar(
        counts,
        shots=shots,
        title=f"Grover results for n4:sa0 (iters={iters}, shots={shots})",
        out_png="figures/grover_counts.png",
    )

    return qc


if __name__ == "__main__":
    main()
