#Idea --> what i'll build --> AND gate with inputs a, b and ancilla c
""" 
    1. 3 qubits: q[0]=a, q[1]=b, q[2]=c (ancilla starts at 0) 
    2. Apply Toffoli ccx(a,b,c) gate
    3. Measure only the ancilla to reporudce the classical AND truth table

    Intuition:
    I'm building four separate circuits (one per input combination). Each of them are indendant; they all start in |000>
    - Circuit #1: input (a,b) = (0,0)
    - Circuit #2: input (a,b) = (0,1)
    - Circuit #3: input (a,b) = (1,0)
    - Circuit #4: input (a,b) = (1,1)

    1024 shots are run per circuit. This gives an histogram of measurement outcomes.

    We run multiple shots because:
        - On a perfect simulator: every shot gives same resault so 1024 is actually redundant
        - on a real quantum hardware: many shots are needed to overcome noise and decoherance; so
            many shots are run to estimate probabilities statistically.

    All four inputs could be run in one circuit simultanesouly by putting 'a' and 'b' in superposition.

    In this example i am basically using the quantum circuit as a reversible logic device. The quantum part
    ensures reversibility but there's no quantum superposition (THE QUBITS ALWAYS START IN DEFINITE 0 or 1 STATES)
"""

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import transpile

def circuit_for_inputs(a: int, b: int):

    #constructor of quantum register that will hold 3 qubits 'q'
    q = QuantumRegister(3, 'q') # q[0]=a, q[1]=b, q[2]=c (ancilla)
    #constructor of classical register to store the MEASURED (collapsed) ancilla bit c which stores the operation a^b
    c = ClassicalRegister(1, 'c_out') #only 1 bit reg to store ancilla
    #constructor of quantum circuit which needs a quantum reg and classical reg
    qc = QuantumCircuit(q, c, name=f"AND_a{a}b{b}")

    # Initialize a and b
    #by default all qubits are initialized to 0 in qiskit, so if for example i pass a a=1,b=0,
    # q[0]==a will be flipped from 0-->1
    # - remember that im building 4 different circuits (one per input vector), and im running 1024 experiments on each circuit
    if a == 1:
        qc.x(q[0])
    if b == 1:
        qc.x(q[1])

    #i then apply Toffoli gate qubits (q[2], the ancilla is already at the 0 state so no need to change it)
    qc.ccx(q[0], q[1], q[2])

    #then we measure the ancilla (we collapse the q[2] qubit) and save it in the classical register
    #this is the classical AND output
    qc.measure(q[2], c[0])
    
    return qc


def run_all_truth_table():
    # Try modern AerSimulator first; fall back to legacy if needed
    backend = None
    try:
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
        runner = "aer_sim"
    except Exception:
        try:
            from qiskit import Aer
            backend = Aer.get_backend('qasm_simulator')
            runner = "qasm_sim"
        except Exception as e:
            print("No simulator backend available. Install qiskit-aer.")
            raise e

    print(f"Using backend: {runner}")

    results = []
    for a in [0, 1]:
        for b in [0, 1]:
            qc = circuit_for_inputs(a, b) #here we build a new circuit for the specific (a,b)
            #compiles for the chosen backend
            #maps high-level gates to backend's basis gates
            #decided qubit layout (whichy physical qubit runs which logical qubit)
            #optimizes gates
            #ensures the circuit is executable on the backend
            tqc = transpile(qc, backend)
            #we exceute the circuit 1024 independent times
            #Each shot: prepare |000⟩ → apply gates → measure → record classical bits
            job = backend.run(tqc, shots=1024)
            #return the histogram of our mesaured ancilla
            counts = job.result().get_counts()
            # counts is over c_out (one bit). Most probable bit is AND.
            #picks the most frequent outcome (for each one of the four circuits)
            and_out = max(counts, key=counts.get)
            results.append((a, b, counts, and_out))

    # Pretty print
    print("\nClassical AND truth table via ancilla measurement (shots=1024):")
    print(" a  b | AND(a,b) | counts")
    print("----+-----------+----------------")
    for a, b, counts, out in results:
        print(f" {a}  {b} |     {out}     | {counts}")

if __name__ == "__main__":
    run_all_truth_table()

