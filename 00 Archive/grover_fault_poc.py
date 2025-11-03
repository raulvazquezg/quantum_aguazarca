from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import Aer

# ---------- Boolean building blocks ----------
def and_into_target(qc, a, b, t):
    # t ^= (a & b)
    qc.ccx(a, b, t)

def xor_into_target(qc, x, t):
    # t ^= x
    qc.cx(x, t)

def or_into_target(qc, x, y, f, t_and):
    """
    Compute f = x OR y into fresh target f, using:
       x OR y = x XOR y XOR (x AND y).
    t_and must start in |0> and is uncomputed back to |0>.
    Assumes f starts in |0>.
    """
    and_into_target(qc, x, y, t_and)    # t_and = x & y
    xor_into_target(qc, x, f)           # f ^= x
    xor_into_target(qc, y, f)           # f ^= y
    xor_into_target(qc, t_and, f)       # f ^= t_and
    and_into_target(qc, x, y, t_and)    # uncompute t_and

def diffuser_on(qc, qin):
    """Grover diffuser on the 3-qubit input register qin."""
    qc.h(qin)
    qc.x(qin)
    # phase flip on |111> (equiv. to Z on |000> in H-basis)
    qc.h(qin[2])
    qc.mcx([qin[0], qin[1]], qin[2])  # 2-control X needs no ancilla
    qc.h(qin[2])
    qc.x(qin)
    qc.h(qin)

# ---------- Build oracle for F=(A&B)|C with D s-a-1 ----------
def build_oracle_circuit():
    # Inputs A,B,C
    qin = QuantumRegister(3, "in")
    # Work: d,f for good; df,ff for faulty; t1,t2 for AND temps
    work = QuantumRegister(6, "w")
    # Flag z = f XOR ff
    flag = QuantumRegister(1, "z")
    # Classical readout for A,B,C
    cout = ClassicalRegister(3, "c")

    qc = QuantumCircuit(qin, work, flag, cout)
    A, B, C = qin[0], qin[1], qin[2]
    d, f, df, ff, t1, t2 = work
    z = flag[0]

    # Put inputs into uniform superposition
    qc.h(qin)

    # --- U_good: compute F into f ---
    and_into_target(qc, A, B, d)           # d = A & B
    or_into_target(qc, d, C, f, t1)        # f = d OR C

    # --- U_fault: inject D s-a-1 and compute F_fault into ff ---
    qc.x(df)                                # df = 1  (D stuck-at-1)
    or_into_target(qc, df, C, ff, t2)       # ff = df OR C = 1

    # Compare outputs into z
    xor_into_target(qc, f, z)               # z ^= f
    xor_into_target(qc, ff, z)              # z ^= ff  -> z = f XOR ff

    # Phase-mark states with z=1 (fault detected)
    qc.z(z)

    # Uncompute comparison and both circuits to clean work bits
    xor_into_target(qc, ff, z)
    xor_into_target(qc, f, z)

    or_into_target(qc, df, C, ff, t2)       # uncompute faulty
    qc.x(df)
    or_into_target(qc, d, C, f, t1)         # uncompute good
    and_into_target(qc, A, B, d)

    return qc, qin, cout

def run_once(shots=2000):
    qc, qin, cout = build_oracle_circuit()
    # One Grover iteration is optimal here (3 marked out of 8)
    diffuser_on(qc, qin)
    #qc.measure(qin, cout)
    qc.measure(qin, cout[::-1])

    backend = Aer.get_backend("qasm_simulator")
    tqc = transpile(qc, backend)
    res = backend.run(tqc, shots=shots).result()
    counts = res.get_counts()

    print("Counts (A B C):", counts)

    # Check: detecting set for D s-a-1 on F=(A&B)|C is {000, 010, 100}
    detecting = {"000", "010", "100"}
    total_marked = sum(v for k, v in counts.items() if k in detecting)
    print(f"Detected patterns weight (out of {shots}): {total_marked}")
    print("Top strings:")
    for k in sorted(counts, key=counts.get, reverse=True)[:5]:
        print(f"  {k}: {counts[k]}", " <-- marked" if k in detecting else "")

if __name__ == "__main__":
    run_once(shots=4000)
