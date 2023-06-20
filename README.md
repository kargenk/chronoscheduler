# ChronoScheduler
ChronoScheduler is a tool of timetable optimization.

# Requirements
* python = "^3.11"
* PuLP = "^2.7.0"
* pandas = "^2.0.2"
* numpy = "^1.24.3"
* openpyxl = "^3.1.2"
* xlrd = "^2.0.1"
* tqdm = "^4.65.0"

# 🌲Directory
<pre>
├───data
│   └───A
│       ├───first
│       │   └───constrains
│       └───second
│           └───constrains
├───notebooks
│
├───outputs
│   └───A
│       ├───first
│       └───second
└───src
</pre>

# 💻Installation
<!-- ## Using Docker
```bash
cd environments
``` -->

## Using Poetry
```bash
# Install the Poetry dependency management tool, skip if installed
# Reference: https://python-poetry.org/docs/#installation
curl -sSL https://install.python-poetry.org | python3 -

# Install the project dependencies
poetry install
```

# Usage
```bash
cd src

# preprocessing for Linear Programing
python preprocessing.py

# Solve the problem
python integer_programming.py
```

# 📝Note
Only one special type of pre-processing is supported yet...

# 🚀Updates
**2023.06.20**
- Readme update

# Author
kargenk(**gengen**)

# ©License
WIP
<!-- ChronoScheduler is under [MIT licence](https://en.wikipedia.org/wiki/MIT_License) -->