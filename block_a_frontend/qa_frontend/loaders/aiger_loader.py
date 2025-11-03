from block_a_frontend.qa_frontend.ir.model import CircuitIR, Node, GateType

#this parses ASCII AIGER that Yosys writes.
#We expand inverted edges into explicit NOT nodes

def load_aag(path: str, name="circuit") -> CircuitIR:
    """
    Minimal AAG loader: supports combinational AIGs (L=0).
    Expands input inversions into NOT nodes.
    """
    with open(path) as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    # Header: aag M I L O A
    hdr = lines[0].split()
    assert hdr[0] == "aag", "Not an ASCII AIGER file"
    _, M, I, L, O, A = hdr
    M, I, L, O, A = map(int, (M, I, L, O, A))
    assert L == 0, "This MVP loader supports combinational (L=0) only."

    idx = 1
    inputs_lits = [int(lines[idx + i]) for i in range(I)]; idx += I
    outputs_lits = [int(lines[idx + i]) for i in range(O)]; idx += O

    and_lines = [lines[idx + i] for i in range(A)]; idx += A
    # Optional symbol table
    pi_names, po_names = {}, {}
    while idx < len(lines):
        s = lines[idx]
        if s[0] == 'i':
            k, nm = s[1:].split(' ', 1); pi_names[int(k)] = nm
        elif s[0] == 'o':
            k, nm = s[1:].split(' ', 1); po_names[int(k)] = nm
        elif s[0] == 'c':
            break
        idx += 1

    nodes: dict[str, Node] = {}
    var_to_net: dict[int, str] = {}       # positive (non-inverted) representative net for var
    inv_cache: dict[str, str] = {}        # net -> not_net

    # Helpers
    def const_net(val: int) -> str:
        nm = f"CONST{val}"
        if nm not in nodes:
            nodes[nm] = Node(nm, GateType.CONST, [], {"value": str(val)})
        return nm

    def ensure_not(net: str) -> str:
        if net in inv_cache:
            return inv_cache[net]
        nname = f"NOT_{net}"
        nodes[nname] = Node(nname, GateType.NOT, [net])
        inv_cache[net] = nname
        return nname

    def lit_to_net(lit: int) -> str:
        # literal 2*var (+1 means inverted)
        var = lit // 2
        inv = (lit % 2 == 1)
        if var == 0:
            base = const_net(0)
        else:
            if var not in var_to_net:
                # create placeholder; real producer may appear later
                var_to_net[var] = f"n{var}"
                # placeholder BUF so it can be used as a source before definition
                if var_to_net[var] not in nodes:
                    nodes[var_to_net[var]] = Node(var_to_net[var], GateType.BUF, [])
            base = var_to_net[var]
        return ensure_not(base) if inv else base

    # Create PI nets
    primary_inputs = []
    for i_idx, lit in enumerate(inputs_lits):
        var = lit // 2
        nm = pi_names.get(i_idx, f"PI{i_idx}")
        net = nm
        var_to_net[var] = net
        nodes[net] = Node(net, GateType.PI, [])
        primary_inputs.append(net)

    # AND nodes (topo order guaranteed in AAG)
    for line in and_lines:
        lhs_s, rhs0_s, rhs1_s = line.split()
        lhs, r0, r1 = int(lhs_s), int(rhs0_s), int(rhs1_s)
        lhs_var = lhs // 2
        lhs_net = f"n{lhs_var}"
        in0 = lit_to_net(r0)
        in1 = lit_to_net(r1)
        nodes[lhs_net] = Node(lhs_net, GateType.AND, [in0, in1])
        var_to_net[lhs_var] = lhs_net

    # POs
    primary_outputs = []
    for o_idx, lit in enumerate(outputs_lits):
        src = lit_to_net(lit)
        nm = po_names.get(o_idx, f"PO{o_idx}")
        nodes[nm] = Node(nm, GateType.PO, [src])
        primary_outputs.append(nm)

    ir = CircuitIR(name=name, primary_inputs=primary_inputs,
                   primary_outputs=primary_outputs,
                   nodes=list(nodes.values()))
    return ir
