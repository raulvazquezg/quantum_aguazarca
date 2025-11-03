import os, subprocess, json, sys, argparse
from aguazarca.blocks.a_frontend.loaders.aiger_loader import load_aag
from aguazarca.blocks.a_frontend.ir.dag import toposort
from aguazarca.blocks.a_frontend.ir.model import CircuitIR, Node, GateType

#CLI to run Yosys and load IR

def run(cmd: list[str]):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("parse")  # Verilog -> AIGER -> IR(JSON)
    p1.add_argument("--in", dest="in_v", required=True)
    p1.add_argument("--out", dest="out_json", required=True)
    p1.add_argument("--name", dest="name", default="circuit")

    p2 = sub.add_parser("topo")   # print topo order for sanity
    p2.add_argument("--in", dest="in_json", required=True)

    args = ap.parse_args()

    if args.cmd == "parse":
        in_v = args.in_v
        out_json = args.out_json
        build_dir = os.path.dirname(out_json) or "."
        os.makedirs(build_dir, exist_ok=True)
        aag_path = os.path.join(build_dir, os.path.splitext(os.path.basename(out_json))[0] + ".aag")

        # 1) Yosys: Verilog -> AIGER (.aag)
        yosys_script = f'read_verilog {in_v}; hierarchy -auto-top; proc; opt; aigmap; write_aiger -ascii {aag_path}'
        run(["yosys", "-p", yosys_script])

        # 2) Load AAG -> IR
        ir = load_aag(aag_path, name=args.name)

        # 3) Dump IR JSON
        data = {
            "name": ir.name,
            "primary_inputs": ir.primary_inputs,
            "primary_outputs": ir.primary_outputs,
            "nodes": [{"name":n.name, "type":n.type.value, "inputs":n.inputs, "attrs":n.attrs} for n in ir.nodes],
        }
        with open(out_json, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote {out_json}")

    elif args.cmd == "topo":
        d = json.load(open(args.in_json))
        from qa_frontend.ir.model import CircuitIR, Node, GateType
        ir = CircuitIR(
            name=d["name"],
            primary_inputs=d["primary_inputs"],
            primary_outputs=d["primary_outputs"],
            nodes=[Node(n["name"], GateType(n["type"]), n.get("inputs",[]), n.get("attrs",{})) for n in d["nodes"]],
        )
        order = toposort(ir)
        print("Topological order:", order)

if __name__ == "__main__":
    main()
