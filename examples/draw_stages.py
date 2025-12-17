from qiskit import QuantumCircuit

# -------------------------
# Helpers (shared)
# -------------------------
def prepare_minus(qc: QuantumCircuit, q: int):
    # |-> = (|0> - |1>)/sqrt(2)
    qc.x(q)
    qc.h(q)

def compute_not_into(qc: QuantumCircuit, inp: int, out: int):
    # out := NOT(inp) into fresh |0> out
    qc.x(out)
    qc.cx(inp, out)

def uncompute_not_into(qc: QuantumCircuit, inp: int, out: int):
    qc.cx(inp, out)
    qc.x(out)

def compute_f_good_aag(qc: QuantumCircuit, A: int, B: int, C: int,
                       n4: int, not_n4: int, not_C: int, n5: int, Fg: int):
    # n4 = A & B
    qc.ccx(A, B, n4)
    # not_n4 = NOT(n4)
    compute_not_into(qc, n4, not_n4)
    # not_C = NOT(C)
    compute_not_into(qc, C, not_C)
    # n5 = not_n4 & not_C
    qc.ccx(not_n4, not_C, n5)
    # Fg = NOT(n5)
    compute_not_into(qc, n5, Fg)

def uncompute_f_good_aag(qc: QuantumCircuit, A: int, B: int, C: int,
                         n4: int, not_n4: int, not_C: int, n5: int, Fg: int):
    # reverse of compute_f_good_aag
    uncompute_not_into(qc, n5, Fg)
    qc.ccx(not_n4, not_C, n5)
    uncompute_not_into(qc, C, not_C)
    uncompute_not_into(qc, n4, not_n4)
    qc.ccx(A, B, n4)

def compute_f_faulty_n4_sa0_aag(qc: QuantumCircuit,
                               not_n4_f: int, not_C: int, n5_f: int, Ff: int):
    # n4 is stuck at 0 => not_n4_f = 1
    qc.x(not_n4_f)
    # n5_f = not_n4_f & not_C
    qc.ccx(not_n4_f, not_C, n5_f)
    # Ff = NOT(n5_f)
    compute_not_into(qc, n5_f, Ff)

def uncompute_f_faulty_n4_sa0_aag(qc: QuantumCircuit,
                                 not_n4_f: int, not_C: int, n5_f: int, Ff: int):
    uncompute_not_into(qc, n5_f, Ff)
    qc.ccx(not_n4_f, not_C, n5_f)
    qc.x(not_n4_f)

def diffuser_3q(qc: QuantumCircuit, A: int, B: int, C: int):
    qc.h([A, B, C])
    qc.x([A, B, C])
    qc.h(C)
    qc.ccx(A, B, C)
    qc.h(C)
    qc.x([A, B, C])
    qc.h([A, B, C])

# -------------------------
# Build stages
# -------------------------
def build_base_circuit():
    """
    Allocate all qubits once so layout stays stable across stages.
    """
    # Inputs
    A, B, C = 0, 1, 2

    # Good network wires
    n4, not_n4, not_C, n5, Fg = 3, 4, 5, 6, 7

    # Faulty network wires
    not_n4_f, n5_f, Ff = 8, 9, 10

    # Detection + phase ancilla
    detect, phase = 11, 12

    qc = QuantumCircuit(13, name="Grover_oracle_build")
    return qc, (A, B, C, n4, not_n4, not_C, n5, Fg, not_n4_f, n5_f, Ff, detect, phase)

def draw_stage(qc: QuantumCircuit, filename: str, fold: int = 60):
    qc.draw(output="mpl", filename=filename, fold=fold)

def main():
    qc, q = build_base_circuit()
    A, B, C, n4, not_n4, not_C, n5, Fg, not_n4_f, n5_f, Ff, detect, phase = q

    # ---------- Slide / Stage 1 ----------
    # Building quantum circuit for the fault-free circuit (AAG forward compute)
    compute_f_good_aag(qc, A, B, C, n4, not_n4, not_C, n5, Fg)
    draw_stage(qc, "figures/stage1_fault_free.png")

    # ---------- Slide / Stage 2 ----------
    # Add the faulty part of the circuit (n4 stuck-at-0)
    compute_f_faulty_n4_sa0_aag(qc, not_n4_f, not_C, n5_f, Ff)
    draw_stage(qc, "figures/stage2_add_faulty.png")

    # ---------- Slide / Stage 3 ----------
    # XOR outputs into detect flag: detect = Fg XOR Ff
    qc.cx(Fg, detect)
    qc.cx(Ff, detect)
    draw_stage(qc, "figures/stage3_xor_detect.png")

    # ---------- Slide / Stage 4 ----------
    # Phase kickback: put 'phase' in |-> and flip it conditioned on detect
    prepare_minus(qc, phase)
    qc.cx(detect, phase)
    draw_stage(qc, "figures/stage4_phase_kickback.png")

    # ---------- Slide / Stage 5 ----------
    # Undo circuit (uncompute): clean detect, faulty, then good (reverse order)
    # Undo detect XOR
    qc.cx(Ff, detect)
    qc.cx(Fg, detect)

    # Undo faulty network
    uncompute_f_faulty_n4_sa0_aag(qc, not_n4_f, not_C, n5_f, Ff)

    # Undo good network
    uncompute_f_good_aag(qc, A, B, C, n4, not_n4, not_C, n5, Fg)

    draw_stage(qc, "figures/stage5_uncompute.png")

    # ---------- Slide / Stage 6 ----------
    # Diffuser on inputs (A,B,C)
    diffuser_3q(qc, A, B, C)
    draw_stage(qc, "figures/stage6_diffuser.png")

    print("Wrote figures/stage1_fault_free.png ... figures/stage6_diffuser.png")

if __name__ == "__main__":
    main()
