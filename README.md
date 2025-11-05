We install venv
`sudo apt-get update`
`sudo apt-get install -y python3-venv`

We create project-local venv (in my case i named it 'qavenv')
`python3 -m venv qavenv`

Activate venv
`source qavenv/bin/activate`

we upgrade build tooling
`python -m pip install -U pip setuptools wheel`

To install current project into python env in dev mode (pip here reads the .toml file); this installs pytest as well ro run unit and integration tests
`python3 -m pip install -e .`

to deactivate venv
`deactivate`

Example to parse (Verilog-->AIGER + JSON)
`qa parse --in examples/toy_f.v --out build/toy_f.ir.json --name toy_f`

Example to print topological order (not rlly necessary but useful later for debuggin); (could also do so with .json)
`qa topo --in build/toy_f.ir.aag`

**TESTING**

Example to evaluate .aag output (doing manaul check tho)
`qa eval --in build/toy_f.ir.aag --vec A=1,B=1,C=0`

Example to evaluate JSON (doing manaul check tho)
`qa eval --in build/toy_f.ir.json --vec A=0,B=0,C=1` (we expect a `1` here)

Installing pytest (i already scripted it in .toml file)
`pip install -e .[dev]`

to run all tests with pytest
`pytest -q`

to run a specific UNIT pytest from a single file (example) {this test only checks eval function in cli.py}
`pytest tests/unit/test_eval_toy_f.py -q`

(or to check INTEGRATION test (basically checking the pipeline with the toy eample i have with pytest))
`pytest tests/integration/test_toy_f_end2end.py -q`

**Dev notes**
aag [max var id] [PIs] [latches] [POs] [ANDs]