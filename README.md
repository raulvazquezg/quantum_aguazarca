We install venv
`sudo apt-get update`
`sudo apt-get install -y python3-venv`

We create project-local venv (in my case i named it 'qavenv')
`python3 -m venv qavenv`

Activate venv
`source qavenv/bin/activate`

we upgrade build tooling
`python -m pip install -U pip setuptools wheel`

To install current project into python env in dev mode (pip here reads the .toml file)
`python3 -m pip install -e .`

to deactivate venv
`deactivate`

Example
`qa parse --in examples/toy_f.v --out build/toy_f.ir.json --name toy_f`