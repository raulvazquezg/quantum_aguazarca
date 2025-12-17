from __future__ import annotations

import argparse
from typing import Dict

from aguazarca.blocks.a_frontend.ir.eval import load_ir_json
from .fault_eval import compare_good_vs_faulty, find_detecting_vectors


def _parse_vec(s: str) -> Dict[str, int]:
    """
    Parse "A=1,B=0,C=1" into {"A":1,"B":0,"C":1}
    """
    out: Dict[str, int] = {}
    if not s.strip():
        return out
    parts = [p.strip() for p in s.split(",")]
    for p in parts:
        if "=" not in p:
            raise ValueError(f"Bad --vec token '{p}'. Use A=1,B=0,...")
        k, v = [x.strip() for x in p.split("=", 1)]
        out[k] = 1 if int(v) else 0
    return out


def main():
    ap = argparse.ArgumentParser(description="Block G: verify stuck-at detection by good vs faulty resimulation.")
    ap.add_argument("--ir", type=str, required=True, help="Path to IR JSON (e.g., build/toy_f.ir.json)")
    ap.add_argument("--fault-net", type=str, required=True, help="Fault site net name (e.g., n4)")
    ap.add_argument("--stuck", type=int, choices=[0, 1], required=True, help="Stuck-at value (0 or 1)")
    ap.add_argument("--vec", type=str, default="", help='Single vector, e.g. "A=1,B=1,C=0"')
    ap.add_argument("--exhaustive", action="store_true", help="Enumerate all PI vectors and print detecting ones.")
    args = ap.parse_args()

    ir = load_ir_json(args.ir)

    if args.exhaustive:
        det = find_detecting_vectors(ir, fault_net=args.fault_net, stuck=args.stuck)
        print(f"Detecting vectors for {args.fault_net}:sa{args.stuck}  (count={len(det)})")
        for r in det:
            vec_str = ",".join(f"{k}={v}" for k, v in r.vec.items())
            diffs_str = "; ".join(f"{po}:{g}->{f}" for po, (g, f) in r.diffs.items())
            print(f"  {vec_str:<20}  diffs: {diffs_str}")
        return

    vec = _parse_vec(args.vec)
    r = compare_good_vs_faulty(ir, vec, fault_net=args.fault_net, stuck=args.stuck)
    vec_str = ",".join(f"{k}={v}" for k, v in r.vec.items())
    print(f"Vector: {vec_str}")
    print(f"Good outputs:   {r.good_outs}")
    print(f"Faulty outputs: {r.faulty_outs}")
    print(f"Detected: {r.detected}")
    if r.detected:
        print("Diffs:")
        for po, (g, f) in r.diffs.items():
            print(f"  {po}: {g} -> {f}")


if __name__ == "__main__":
    main()
