![Github](https://img.shields.io/github/tag/kupuguy/dwarf_copier.svg)
![PyPi](https://img.shields.io/pypi/v/dwarf_copier.svg)
![Python](https://img.shields.io/pypi/pyversions/dwarf_copier.svg)
![CI](https://github.com/kupuguy/dwarf_copier/actions/workflows/poetry.yml/badge.svg)

> Note: some badges above will not work until Github CI has been set up and the app is published in Pypi

# Introduction

The dwarf_copier project gives a straightforward way to extract image files from a Dwarf II smart telescope onto a PC for further processing (e.g. using Siril) or as a backup.

# Development Tools

There are multiple good Python IDE, but I'm would suggest using [vscode](https://code.visualstudio.com/) with at least these plugins:

- [Python](vscode:extension/ms-python.python) to add _python_ language support
- [Mypy](vscode:extension/ms-python.mypy-type-checker) for type checking
- [ruff](vscode:extension/charliermarsh.ruff) formatting and linting your code
- [even-better-toml](vscode:extension/tamasfe.even-better-toml) for a better _TOML_ file support (and poetry configuration file is a _toml_ file)
- [textual](vscode:extension/Textualize.textual-syntax-highlighter) validates Textual's CSS

[Poetry](https://python-poetry.org) is used to handle dependencies:

- `poetry add` to add a new dependencies
- `poetry install` to create a _virtualenv_ with all needed libraries to run your app
- `poetry shell` to enter your _virtualenv_ and run your app or tests
- `poetry build` to create a distributable binary package of your app


## Run the tests

To run the tests, you need to be in the _virtualenv_ then just run `tox` or `pytest`:

```sh
# init your virtualenv if it is not
$ poetry install

# enter your virtualenv
$ poetry shell

# note that your shell prompt is updated once you are in a virtualenv
(dwarf_copier-py3.10) $ pytest
====================================== test session starts ======================================
platform linux -- Python 3.10.13, pytest-7.2.0, pluggy-1.0.0
rootdir: /home/kupuguy/dwarf_copier
plugins: dotenv-0.5.2, cov-4.0.0
collected 3 items

tests/test_cli.py ...                                                                     [ 66%]
tests/test_user.py .                                                                      [100%]

======================================= 3 passed in 0.07s =======================================
```

## Build your app

You can use _Poetry_ to build the app and get a `.whl`

```sh
$ poetry build
Building cool-project (0.1.0)
  - Building sdist
  - Built cool_project-0.1.0.tar.gz
  - Building wheel
  - Built cool_project-0.1.0-py3-none-any.whl

$ ls -l dist
total 20
-rw-r--r-- 1 seb users 8569 17 oct.  11:12 cool_project-0.1.0-py3-none-any.whl
-rw-r--r-- 1 seb users 7484 17 oct.  11:12 cool_project-0.1.0.tar.gz
```

## Publish your app

You can use _Poetry_ to publish your app to [PyPI](https://pypi.org)

```sh
$ poetry publish
```

By default, _Github Actions_ are configured to

- build your app and run your unit tests with coverage on every push
- build the wheel package and upload it to Pypi on every tag

> Note: to allow Github CI to publish on PyPI, you need to [create a token](https://pypi.org/manage/account/token/) and add it to [your project settings](https://github.com/essembeh/python-dwarf_copier/settings/secrets/actions), the name of the token should be `PYPI_TOKEN`

I personnally use this command to bump the version using poetry, create the associated git tag and push to Github:

```sh
# for a patch bump
$ poetry version patch && git commit -a -m '🔖 New release' && git tag -f $(poetry version -s) && git push --tags
# for a minor bump
$ poetry version minor && git commit -a -m '🔖 New release' && git tag -f $(poetry version -s) && git push --tags
# for a major bump
$ poetry version major && git commit -a -m '🔖 New release' && git tag -f $(poetry version -s) && git push --tags
```

## How to install your app

Install from the sources

```sh
$ pip3 install poetry
$ pip3 install git+https://github.com/jdoe/cool-project
$ cool-command --help
```

Install from [PyPI](https://pypi.org/) if you published it

```sh
$ pip3 install cool-project
$ cool-command --help
```

# TODO - clean this up!
# Start a new project from scratch

```sh
# create the new project folder
$ mkdir cool-project && cd cool-project

# create a README
$ cat << EOF >> README.md
Here is my cool project
EOF

# configure excluded files
$ cat << EOF >> .gitignore
# Generated files
__pycache__
*.pyc
/.pytest_cache
/.coverage*
/dist
# IDE configuration
/.vscode/*
!/.vscode/settings.json
EOF

# init the root python module
$ mkdir cool_project
$ cat << EOF >> cool_project/__init__.py
from importlib.metadata import version

__version__ = version(__name__)
EOF

# create the first commit
$ git init
$ git add .
$ git commit -m "🚀 First release"

# init the poetry pyproject.toml
$ poetry init -n

# configure poetry to create the virtualenv dir in the project folder
$ cat << EOF >> poetry.toml
[virtualenvs]
in-project = true
EOF

# create the virtualenv
$ poetry shell

# add some runtime dependencies
$ poetry add colorama

# add some development dependencies
$ poetry add --group dev black isort pylint pytest pytest-cov pytest-dotenv

# install your package
$ poetry install

# test that your app is installed in your virtualenv
$ python -c 'import cool_project; print(cool_project.__version__)'

```

Snippet to add an _entrypoint_

```toml
[tool.poetry.scripts]
mycommand = 'cool_project.cli:run'
```
