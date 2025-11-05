import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path

from aguazarca.blocks.a_frontend.loaders.aiger_loader import load_aag
from aguazarca.blocks.a_frontend.ir.dag import toposort
from aguazarca.blocks.a_frontend.ir.eval import load_ir_json, eval_vec


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)


def _load_ir_from_path(p: Path, *, name_from_stem: bool = True):
    """Load CircuitIR from either an AIGER (.aag/.aig) or our IR .json file."""
    if p.suffix.lower() in {".aag", ".aig"}:
        return load_aag(str(p), name=p.stem if name_from_stem else "circuit")
    else:
        return load_ir_json(str(p))


def main() -> None:
    ap = argparse.ArgumentParser(description="QA Block A CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # parse: Verilog -> AIGER (.aag) + IR (JSON)
    p1 = sub.add_parser("parse", help="Verilog -> AIGER (.aag) and IR JSON")
    p1.add_argument("--in", dest="in_v", required=True, help="Input Verilog file")
    p1.add_argument("--out", dest="out_json", required=True, help="Output IR JSON path")
    p1.add_argument("--name", dest="name", default="circuit", help="Logical circuit name")

    # topo: print evaluation order from .aag/.aig or .json
    p2 = sub.add_parser("topo", help="Show topological order for given artifact")
    p2.add_argument("--in", dest="in_art", required=True, help="Input .aag/.aig or IR .json")

    # eval: evaluate outputs for a given PI vector
    p3 = sub.add_parser("eval", help="Evaluate circuit for given PI vector")
    p3.add_argument("--in", dest="in_art", required=True, help="Input .aag/.aig or IR .json")
    p3.add_argument(
        "--vec",
        dest="vec",
        required=True,
        help="Comma list of PI assignments, e.g. A=1,B=1,C=0 (or PI0=1,PI1=0,...)",
    )

    args = ap.parse_args()

    if args.cmd == "parse":
        in_v = args.in_v
        out_json = args.out_json

        build_dir = os.path.dirname(out_json) or "."
        os.makedirs(build_dir, exist_ok=True)

        # Write the AIGER next to the JSON, sharing the base name
        base = os.path.splitext(os.path.basename(out_json))[0]
        aag_path = os.path.join(build_dir, base + ".aag")

        # Yosys script: canonicalize to AIG and preserve symbols (PI/PO names)
        yosys_script = (
            f"read_verilog {in_v}; "
            f"hierarchy -auto-top; proc; opt; "
            f"aigmap; write_aiger -ascii -symbols {aag_path}"
        )
        run(["yosys", "-p", yosys_script])

        # Load the freshly written AAG into our IR and dump JSON (debug snapshot)
        ir = load_aag(aag_path, name=args.name)
        data = {
            "name": ir.name,
            "primary_inputs": ir.primary_inputs,
            "primary_outputs": ir.primary_outputs,
            "nodes": [
                {"name": n.name, "type": n.type.value, "inputs": n.inputs, "attrs": n.attrs}
                for n in ir.nodes
            ],
        }
        with open(out_json, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wrote {out_json}")

    elif args.cmd == "topo":
        p = Path(args.in_art)
        ir = _load_ir_from_path(p)
        order = toposort(ir)
        print("Topological order:", order)

    elif args.cmd == "eval":
        p = Path(args.in_art)
        ir = _load_ir_from_path(p)

        # Parse vector "A=1,B=0,..." (robust to accidental spaces)
        parts = [kv.strip() for kv in args.vec.split(",") if kv.strip()]
        vec_raw = dict(kv.split("=", 1) for kv in parts)

        # Normalize optional PI0/PI1/... to actual input names (e.g., "A","B","C")
        pi_order = ir.primary_inputs  # e.g., ["A","B","C"]
        vec_norm: dict[str, int] = {}
        for k, v in vec_raw.items():
            m = re.fullmatch(r"PI(\d+)", k)
            if m:
                idx = int(m.group(1))
                if 0 <= idx < len(pi_order):
                    k = pi_order[idx]
            vec_norm[k] = int(v) & 1

        # Optional: warn on unknown inputs (helps catch typos)
        unknown = sorted(set(vec_norm) - set(pi_order))
        if unknown:
            print(
                f"Warning: unknown inputs {unknown}; known PIs: {pi_order}",
                file=sys.stderr,
            )

        out = eval_vec(ir, vec_norm)
        print(out)


if __name__ == "__main__":
    main()
