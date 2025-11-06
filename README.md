**INSTALLATION**
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

**RUNNING BLOCK A**

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

This test allows me to prove functional equivalence between a .v file and and .aag using built-in equivalence tests that Yosys has (it grabs .aag file from build/ so i can edit it and make it fail if i wanted to) {example with c17 ISCAS'85 benchmark circuit}
```
yosys -p '
  read_verilog examples/c17.v; prep -top c17; rename -top gold; design -stash gold
  read_aiger   build/c17.ir.aag; prep -auto-top; rename -top gate; design -stash gate
  design -copy-from gold -as gold gold
  design -copy-from gate -as gate gate
  equiv_make gold gate equiv
  hierarchy -top equiv
  equiv_struct
  equiv_simple
  equiv_induct -undef
  equiv_status -assert
'
```

**VISUALIZATION**
To visualize verilog file with Yosys (example)
`yosys -p 'read_verilog examples/toy_f.v; hierarchy -auto-top; proc; opt; clean; show'`
OR
`yosys -p 'read_verilog examples/toy_f.v; hierarchy -auto-top; show -format dot -prefix build/toy_v'`
`dot -Tsvg build/toy_v.dot -o build/toy_v.svg`

To visualize AAG file with Yosys (example) - [ofc verify with topological order command]
`yosys -p 'read_aiger build/toy_f.ir.aag; hierarchy -auto-top; show -format dot -viewer xdot'`
OR
`yosys -p 'read_aiger build/toy_f.ir.aag; show -format dot -prefix build/toy_aig'`
`dot -Tsvg build/toy_aig.dot -o build/toy_aig.svg`


**Dev notes**
aag [max var id] [PIs] [latches] [POs] [ANDs]