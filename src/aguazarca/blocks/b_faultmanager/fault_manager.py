from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from aguazarca.blocks.a_frontend.ir.model import CircuitIR, GateType, Node
from .fault_model import Cone, Fault, FaultSite, FaultType


class FaultManager:
    """
    Block B (Fault manager) for your current CircuitIR.

    Responsibilities:
      1) Enumerate fault sites (default: PI + AND; optionally include PO)
      2) Enumerate stuck-at faults (sa0/sa1)
      3) Compute fan-out cones using the IR connectivity (net-name graph)
      4) Provide easy selection for the demo (e.g., pick n4 sa0)
    """

    def __init__(self, ir: CircuitIR):
        self.ir = ir
        self.nodes_by_name: Dict[str, Node] = {n.name: n for n in ir.nodes}

        # Build fanout adjacency: net -> list of nets that depend on it
        self.fanout: Dict[str, List[str]] = self._build_fanout()

        # For convenience: PO driver mapping
        self.po_drivers: Dict[str, str] = self._build_po_drivers()

    # ---------- Core graph helpers ----------

    def _build_fanout(self) -> Dict[str, List[str]]:
        fanout: Dict[str, List[str]] = {}
        for n in self.ir.nodes:
            for src in n.inputs:
                fanout.setdefault(src, []).append(n.name)
        return fanout

    def _build_po_drivers(self) -> Dict[str, str]:
        """
        In your IR, PO is a node with one input: its driver net.
        """
        out: Dict[str, str] = {}
        for n in self.ir.nodes:
            if n.type == GateType.PO:
                if not n.inputs:
                    raise ValueError(f"PO node '{n.name}' has no driver input.")
                out[n.name] = n.inputs[0]
        return out

    # ---------- Public API ----------

    def enumerate_sites(
        self,
        include_pis: bool = True,
        include_ands: bool = True,
        include_pos: bool = False,
    ) -> List[FaultSite]:
        sites: List[FaultSite] = []
        for n in self.ir.nodes:
            if n.type == GateType.PI and include_pis:
                sites.append(FaultSite(net=n.name, kind="PI"))
            elif n.type == GateType.AND and include_ands:
                sites.append(FaultSite(net=n.name, kind="AND"))
            elif n.type == GateType.PO and include_pos:
                sites.append(FaultSite(net=n.name, kind="PO"))
        return sites

    def fanout_cone(self, site: FaultSite) -> Cone:
        """
        Fan-out cone = all nets reachable from site.net by walking fanout edges.
        Outputs are included if their PO node depends (directly or indirectly) on the site.
        """
        start = site.net
        visited: Set[str] = set()
        stack: List[str] = [start]

        while stack:
            u = stack.pop()
            if u in visited:
                continue
            visited.add(u)
            for v in self.fanout.get(u, []):
                stack.append(v)

        # Determine which primary outputs are affected.
        # A PO is affected if its PO node or its driver chain is in the visited set.
        affected: List[str] = []
        for po in self.ir.primary_outputs:
            # In your IR, po is also a Node.name (GateType.PO).
            # If the PO node itself is reachable, it's affected.
            if po in visited:
                affected.append(po)
                continue
            # Otherwise check if its driver net is reachable.
            drv = self.po_drivers.get(po)
            if drv is not None and drv in visited:
                affected.append(po)

        return Cone(nets=frozenset(visited), outputs=tuple(affected))

    def enumerate_faults(
        self,
        include_pis: bool = True,
        include_ands: bool = True,
        include_pos: bool = False,
    ) -> List[Fault]:
        faults: List[Fault] = []
        for site in self.enumerate_sites(include_pis, include_ands, include_pos):
            cone = self.fanout_cone(site)
            faults.append(Fault(site=site, ftype=FaultType.SA0, cone=cone))
            faults.append(Fault(site=site, ftype=FaultType.SA1, cone=cone))
        return faults

    def pick_fault(
        self,
        net: str,
        ftype: FaultType = FaultType.SA0,
        include_pis: bool = True,
        include_ands: bool = True,
        include_pos: bool = False,
    ) -> Fault:
        """
        Select one fault for demo by net name (e.g., 'n4') and type.
        """
        # Validate that net is a legal site under current include flags
        allowed = {s.net: s for s in self.enumerate_sites(include_pis, include_ands, include_pos)}
        if net not in allowed:
            raise ValueError(
                f"Net '{net}' is not an enabled fault site. Enabled sites: {list(allowed.keys())}"
            )
        site = allowed[net]
        return Fault(site=site, ftype=ftype, cone=self.fanout_cone(site))
