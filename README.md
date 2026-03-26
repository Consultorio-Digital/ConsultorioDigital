## BUILD

Before running setup, **install pyenv and Poetry to manage the Python version and dependencies**. **See the next sections for more information**.

### Special note for WSL

If using WSL, first change permissions of the project folder:

```bash
sudo chown -R your_username /path/to/salud_publica_digital
```

To build, run the setup.py file with Python 3.11.8 environment activated (`pyenv activate YOUR_ENVIRONMENT`), and with all the dependencies installed via Poetry (`poetry install`). 

Then run:

```bash
python ./setup.py --local
```

Where can pass the following arguments:

```bash
--local: To build local resources and download metadata from endpoints.
--googlecloud: To build google cloud resources.
```

Before exit, make sure to deactivate venv:

```bash
pyenv deactivate
```

For first time setup, must run with --local argument.

## DEPENDENCIES

salud_publica_digital uses [Poetry](https://python-poetry.org), which is a packaging and dependency management tool for Python projects. With Poetry, dependency management is made much easier.

### PYTHON VERSION

Python 3.11.8.

#### LINUX or MAC

##### Specific note to LINUX

Previous to install any Python version, must install the following dependencies:

```bash
sudo apt-get install build-essential
sudo apt install libssl-dev libffi-dev libncurses5-dev zlib1g zlib1g-dev libreadline-dev libbz2-dev libsqlite3-dev make gcc
sudo apt-get install liblzma-dev
```

First install pyenv with the following command (if already have pip, can install with pip by running `pip install pyenv`):

```bash
curl https://pyenv.run | bash
```

Then add to `~/.bash_profile` or `~/.bashrc` for adding pyenv to the PATH:

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"
```

For loading `pyenv-virtualenv` plugin, add to `~/.bash_profile` or `~/.bashrc`:

```bash
export PYENV_ROOT="$HOME/.pyenv"
eval "$(pyenv virtualenv-init -)"
```

Then restart your shell and follow the next steps.

#### INSTALLING A VIRTUAL ENVIRONMENT

To install Python 3.11.8 in an isolated env (to not collide with your main Python version), use pyenv:

```bash
pyenv install 3.11.8
```

Then, create a virtual environment with the following command:

```bash
pyenv virtualenv 3.11.8 salud_publica_digital
```

Lastly, activate the virtual environment with the following command:

```bash
pyenv activate salud_publica_digital
```

Then, proceed to install the dependencies with Poetry (if not installed, see the next section) with the following command:

```bash
poetry install
```

Done! Now you can run the project with the Python version 3.11.8.

### POETRY

Poetry is used to install the dependencies in a virtual environment if the user does not want to install the dependencies on their local environment.

#### INSTALLING POETRY

To install Poetry, install `pipx` first. If it is not installed, it can be installed with the following command:

```bash
pip install pipx
```

Then, install Poetry with the following command:

```bash
pipx install poetry
```

Then, add the Poetry bin to the PATH with the following command:

```bash
pipx ensurepath
```

Restart your shell and you are ready to use Poetry.

#### INSTALLING DEPENDENCIES

Go to the root of the project and run:

```bash
poetry install
```

Note that Poetry will create a virtual environment for the project and install the dependencies in it. If you want to install the dependencies on your local environment, please use PIP method.

Is recommended to use Poetry in conjunction with pyenv to manage the Python versions. For this, just activate the virtual environment with pyenv and then run the Poetry commands.

## SETTING UP DJANGO

First, install `django` with the following command:

```bash
poetry add django
```

After installing pyenv and Poetry, go to [this url](https://builtwithdjango.com/blog/basic-django-setup).

Then, go to `salud_publica_digital` folder and run the following command:

```bash
poetry run python manage.py runserver
```

After running, you should see this message:

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).

You have 18 unapplied migration(s). Your project may not work properly until you apply the migrations for app(s): admin, auth, contenttypes, sessions.
Run 'python manage.py migrate' to apply them.
```

For getting rid of the migrations message, run the following command:

```bash
poetry run python manage.py migrate
```

You are ready to go!

### CREATING A DJANGO APP

To create a Django app, run the following command:

```bash
poetry run python manage.py startapp YOUR_APP_NAME
```

Then, add the app to the `INSTALLED_APPS` list in the `settings.py` file.

### LOADING HEALTH DATA

First, execute `data.py` file which will download data from the Ministry of Environment from ARCGIS (https://arcgis.mma.gob.cl/server/rest/services/IDE/Cartografia_Base/FeatureServer) and save it to `utils/data/geo_data.json`:

Then, load the data to the database with the following command:

```bash
poetry run python manage.py loaddata utils/data/geodata.json
```