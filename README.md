# e2xgit

This package provides functionality for automatically committing files on a Jupyter server

## Installation

```
git clone https://github.com/Digiklausur/e2xgit
cd e2xgit
pip install .
```

## Register the hooks

Add the following lines to your `jupyter_notebook_config.py`:

```
from e2xgit import configure_e2xgit

c = get_config()

...

configure_e2xgit(c)
```
