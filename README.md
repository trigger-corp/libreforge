# Forge Platform


## Installation

### Install `pyenv`:

    curl https://pyenv.run | bash

### Install Python 2.7.18:

    pyenv install 2.7.18

Remember to add the following to your shell startup script: (`~/.zshenv` for `zsh`)

     export PATH="~/.pyenv/bin:$PATH"
     eval "$(pyenv init --path)"      # <-- fixes setup.py paths
     eval "$(pyenv init -)"
     eval "$(pyenv virtualenv-init -)"

### Create libreforge python environment:

    git clone https://github.com/trigger-corp/libreforge.git libreforge.git
    cd libreforge.git

    pyenv virtualenv 2.7.18 libreforge
    pyenv local libreforge

### Install python dependencies:

    pip install -r generate/requirements.txt




Requires python 2.7 and virtualenv::

    virtualenv ./python-env
    source python-env/bin/activate ("python-env/Scripts/activate.bat" on windows)
    cd generate
    pip install -r requirements.txt
    python setup.py develop


## Commands

All commands have their own help, run with -h for detaisl

`forge-generate`, `forge-inspector`, `forge-module-test-app`
