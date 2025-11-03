from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit import transpile

qc = QuantumCircuit(2, 2)
qc.h(0); qc.cx(0,1)
qc.measure([0,1], [0,1])

backend = Aer.get_backend("qasm_simulator")
tqc = transpile(qc, backend)
res = backend.run(tqc, shots=2000).result()
print(res.get_counts())
