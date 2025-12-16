from __future__ import annotations
import argparse
from pathlib import Path

from aguazarca.blocks.a_frontend.ir.eval import load_ir_json
from .fault_manager import FaultManager
from .fault_model import FaultType


def main():
    ap = argparse.ArgumentParser(description="Block B: Enumerate stuck-at faults and fanout cones on CircuitIR.")
    ap.add_argument("--ir", type=str, required=True, help="Path to IR JSON (e.g., build/toy_f.ir.json)")
    ap.add_argument("--list-sites", action="store_true", help="List candidate fault sites.")
    ap.add_argument("--list-faults", action="store_true", help="List all faults and their cones.")
    ap.add_argument("--pick", type=str, default=None, help="Pick one fault site by net name (e.g., n4).")
    ap.add_argument("--sa", type=str, default="sa0", choices=["sa0", "sa1"], help="Fault type for --pick.")
    ap.add_argument("--no-pis", action="store_true", help="Exclude PI sites.")
    ap.add_argument("--no-ands", action="store_true", help="Exclude AND sites.")
    ap.add_argument("--include-pos", action="store_true", help="Include PO sites (off by default).")
    args = ap.parse_args()

    ir = load_ir_json(args.ir)
    fm = FaultManager(ir)

    include_pis = not args.no_pis
    include_ands = not args.no_ands
    include_pos = args.include_pos

    if args.list_sites:
        sites = fm.enumerate_sites(include_pis=include_pis, include_ands=include_ands, include_pos=include_pos)
        for s in sites:
            print(f"{s.net:>12}  kind={s.kind}")
        return

    if args.list_faults:
        faults = fm.enumerate_faults(include_pis=include_pis, include_ands=include_ands, include_pos=include_pos)
        for f in faults:
            nets = ",".join(sorted(f.cone.nets))
            outs = ",".join(f.cone.outputs) if f.cone.outputs else "(none)"
            print(f"{f.id_str:>12}  outs={outs:<10}  cone=[{nets}]")
        return

    if args.pick:
        ftype = FaultType.SA0 if args.sa == "sa0" else FaultType.SA1
        fault = fm.pick_fault(
            net=args.pick,
            ftype=ftype,
            include_pis=include_pis,
            include_ands=include_ands,
            include_pos=include_pos,
        )
        nets = ",".join(sorted(fault.cone.nets))
        outs = ",".join(fault.cone.outputs) if fault.cone.outputs else "(none)"
        print(f"Picked fault: {fault.id_str}")
        print(f"  site kind: {fault.site.kind}")
        print(f"  affected outputs: {outs}")
        print(f"  fanout cone nets: [{nets}]")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
