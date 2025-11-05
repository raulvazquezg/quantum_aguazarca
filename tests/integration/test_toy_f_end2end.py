import ast
import shutil
import subprocess
from pathlib import Path
import pytest

#note that this test only check the parsed logic (immediate rep IR) in .aag format of the first circuit i tested
#this pipeline with which is in examples/toy_f.v (after building generated file build/toy_f.ir.aag)

pytestmark = pytest.mark.integration

@pytest.mark.skipif(shutil.which("yosys") is None, reason="yosys not installed")
def test_parse_and_eval_from_aag(tmp_path: Path):
    repo = Path(__file__).resolve().parents[2]
    verilog = repo / "examples" / "toy_f.v"
    out_json = tmp_path / "toy_f.ir.json"   # CLI needs this arg; we will ignore the JSON
    aag = tmp_path / "toy_f.ir.aag"         # parse() will emit this next to JSON

    # 1) Produce AIGER via CLI (Verilog -> AIGER)
    subprocess.run(
        ["qa", "parse", "--in", str(verilog), "--out", str(out_json), "--name", "toy_f"],
        check=True,
        text=True,
    )

    # 2) Sanity-check the AAG symbols exist (names we rely on)
    txt = aag.read_text()
    assert "i0 A" in txt and "i1 B" in txt and "i2 C" in txt and "o0 F" in txt
    assert txt.splitlines()[0].startswith("aag ")

    # 3) Evaluate directly from the .aag via CLI
    def cli_eval(vec):
        cp = subprocess.run(
            ["qa", "eval", "--in", str(aag), "--vec", vec],
            check=True, capture_output=True, text=True
        )
        return ast.literal_eval(cp.stdout.strip())

    assert cli_eval("A=1,B=1,C=0")["F"] == 1
    assert cli_eval("A=0,B=0,C=1")["F"] == 1
    assert cli_eval("A=1,B=0,C=0")["F"] == 0
