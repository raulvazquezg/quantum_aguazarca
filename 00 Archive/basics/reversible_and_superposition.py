# reversible_and_superposition.py
# Prepare a and b in superposition, compute AND into ancilla via Toffoli (ccx),
# then measure ancilla (and optionally all qubits).

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile

def build_superposition_and_circuit(measure_all=False):
    """
    Build a single circuit that:
      - prepares q[0], q[1] in equal superposition with H
      - ancilla q[2] starts at |0>
      - applies Toffoli to compute a AND b into ancilla
      - measures ancilla (and optionally measures a and b too)
    """
    q = QuantumRegister(3, 'q')      # q[0]=a, q[1]=b, q[2]=c (ancilla)
    if measure_all:
        c = ClassicalRegister(3, 'c') # measure all three qubits
    else:
        c = ClassicalRegister(1, 'c') # measure ancilla only
    qc = QuantumCircuit(q, c, name="AND_superposition")

    # --- DIFFERENCE from previous code: put a and b in superposition
    qc.h(q[0])
    qc.h(q[1])

    # ancilla is left in |0> (no qc.x on q[2] here)
    qc.ccx(q[0], q[1], q[2])

    # measure: either only ancilla (classical result = AND) or all qubits
    if measure_all:
        qc.measure(q[2], c[0])  # ancilla → first (leftmost in printed string)
        qc.measure(q[1], c[1])  # b
        qc.measure(q[0], c[2])  # a → last (rightmost in printed string)

    else:
        qc.measure(q[2], c[0])  # measure ancilla only

    return qc

def run_superposition_demo(shots=1024, measure_all=False):
    from qiskit_aer import AerSimulator
    backend = AerSimulator() # statevector and qasm features available
  
    qc = build_superposition_and_circuit(measure_all=measure_all)

    # transpile/compile step (same role as before)
    tqc = transpile(qc, backend)

    # run as a shot-based experiment (qasm style)
    job = backend.run(tqc, shots=shots)
    counts = job.result().get_counts()
    return qc, counts

if __name__ == "__main__":
    print("Running superposition version (measure ancilla only) ...")
    qc, counts = run_superposition_demo(shots=1024, measure_all=False)
    print("Counts (ancilla):", counts)

    print("\nmeasuremnt of all qubits to see distribution ...")
    qc_all, counts_all = run_superposition_demo(shots=1024, measure_all=True)
    print("Counts (a b ancilla):", counts_all)
