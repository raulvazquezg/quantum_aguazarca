import shutil
import subprocess
from pathlib import Path
import pytest

pytestmark = pytest.mark.integration

@pytest.mark.skipif(shutil.which("yosys") is None, reason="yosys not installed")
def test_equiv_c17(tmp_path: Path):
    repo = Path(__file__).resolve().parents[2]
    verilog = repo / "examples" / "c17.v"
    assert verilog.exists(), f"Missing {verilog}"

    out_json = tmp_path / "c17.ir.json"   # CLI wants an --out JSON path
    aag_gate = tmp_path / "c17.ir.aag"    # qa parse will emit this next to JSON

    # 1) Verilog -> AIGER (.aag) via our CLI (hermetic: write into tmp_path)
    subprocess.run(
        ["qa", "parse", "--in", str(verilog), "--out", str(out_json), "--name", "c17"],
        check=True, text=True
    )
    assert aag_gate.exists()

    # 2) Yosys formal equivalence: gold = RTL, gate = our AIGER
    yos = f"""
      read_verilog {verilog}; prep -top c17; rename -top gold; design -stash gold
      read_aiger   {aag_gate}; prep -auto-top; rename -top gate; design -stash gate
      design -copy-from gold -as gold gold
      design -copy-from gate -as gate gate
      equiv_make gold gate equiv
      hierarchy -top equiv
      equiv_struct
      equiv_simple
      equiv_induct -undef
      equiv_status -assert
    """
    subprocess.run(["yosys", "-q", "-p", yos], check=True, text=True)

    # 3) (Optional) ABC CEC backstop: AIG vs AIG
    aag_gold = tmp_path / "c17.gold.aag"
    yos_gold = f"""
      read_verilog {verilog}; prep -top c17; aigmap;
      write_aiger -ascii {aag_gold}
    """
    subprocess.run(["yosys", "-q", "-p", yos_gold], check=True, text=True)

    abc = shutil.which("abc") or shutil.which("yosys-abc")
    if abc:
        subprocess.run([abc, "-c", f"read_aiger {aag_gold}; read_aiger {aag_gate}; cec"],
                       check=True, text=True)
    else:
        pytest.skip("ABC not available (looking for `abc` or `yosys-abc`).")
