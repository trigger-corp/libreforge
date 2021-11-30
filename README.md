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

### Install `forge-*` commands:

    cd libreforge.git/generate
    pip install -r requirements.txt
    python setup.py develop

### Configure installation:

Link module directory:

    cd libreforge.git
    ln -s ../modules ./modules.local

Create a new file: `libreforge.git/system_config.json`

    {
        "android_sdk_root": "/mnt/android-sdks",
        "android_sdk_dir": "/mnt/android-sdks/api-30",
        "module_urls": "https://s3.amazonaws.com/trigger-module-build/%s/%s.zip",
        "xcode_version": "/Applications/Xcode.app"
    }

Create or copy `local_config.json`:

    cd libreforge.git
    cp path/to/your/app/local_config.json path/to/libreforge.git/local_config.json


## Commands

All commands have their own help, run with -h for details:

* `forge-generate`  - build or package an app
* `forge-inspector` - generates or re-generates a module's inspector app
* `forge-module-test-app` - generates an app that will run module tests


### `forge-generate`

To build an app, set the PLATFORM environment variable to one of:

    export PLATFORM=android
    export PLATFORM=ios

Then:

    export PROJECT=vanilla

Remember to delete the target directories:

    rm -rf ~/forge-workspace/$PROJECT/development

Then build the app:

    forge-generate build -p -v --platforms $PLATFORM \
                   --config ~/forge-workspace/$PROJECT/src/config.json \
                   --usercode ~/forge-workspace/$PROJECT/src \
                   --userassets ~/forge-workspace/$PROJECT/assets \
                   --override_modules modules.local \
                   --temp=/tmp/libreforge \
                   --output ~/forge-workspace/$PROJECT

To package an app:

    rm -rf ~/forge-workspace/$PROJECT/development
    rm -rf ~/forge-workspace/$PROJECT/release

    forge-generate build package -p -v --platforms $PLATFORM \
                   --config ~/forge-workspace/$PROJECT/src/config.json \
                   --usercode ~/forge-workspace/$PROJECT/src \
                   --userassets ~/forge-workspace/$PROJECT/assets \
                   --override_modules modules.local \
                   --temp=/tmp/libreforge \
                   --output ~/forge-workspace/$PROJECT

For iOS, if you are not logged into a local shell, you may also need to do a:

    security -v unlock-keychain -p <password> /Library/Keychains/System.keychain
    security -v unlock-keychain -p <password> ~/Library/Keychains/login.keychain-db
