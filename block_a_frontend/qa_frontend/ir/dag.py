from collections import defaultdict, deque
from block_a_frontend.qa_frontend.ir.model import CircuitIR

def toposort(ir: CircuitIR) -> list[str]:
    fanin = {n.name: list(n.inputs) for n in ir.nodes}
    fanout = defaultdict(list)
    for n in ir.nodes:
        for a in n.inputs:
            fanout[a].append(n.name)
    indeg = {k: len(v) for k, v in fanin.items()}
    q = deque([k for k, d in indeg.items() if d == 0])
    order, seen = [], set()
    while q:
        u = q.popleft()
        if u in seen: continue
        seen.add(u); order.append(u)
        for v in fanout[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order
