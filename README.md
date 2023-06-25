# ChronoScheduler
ChronoScheduler is a tool of timetable optimization.

# Requirements
* python = "^3.10"
* PuLP = "^2.7.0"
* pandas = "^2.0.2"
* numpy = "^1.24.3"
* openpyxl = "^3.1.2"
* xlrd = "^2.0.1"
* fastapi = "^0.98.0"
* uvicorn = {extras = ["standard"], version = "^0.22.0"}

# 🌲Directory
<pre>
chronoscheduler
├───api                   : フロントエンド
│
├───data
│   └───toy              : 授業情報、時限、教室ファイル
│       └───constraints  : 制約ファイル
│
├───environments          : Dockerfileなどの実行環境
│
├───notebooks             : 実験と可視化用ノートブック
│
├───outputs
│   └───toy              : 最適化後の時間割ファイル
│
└───src                   : ソースコード
</pre>

# 💻Installation
Clone this repository.
```bash
git clone https://github.com/kargenk/chronoscheduler.git
```

## Using Poetry
```bash
# Install the Poetry dependency management tool, skip if installed
# Reference: https://python-poetry.org/docs/#installation
curl -sSL https://install.python-poetry.org | python3 -
```

# Usage
Create environment with Poetry:
```bash
cd chronoscheduler/src

# Activate venv and Install the project dependencies
poetry shell
poetry install
```

Make mock data and solve the problem:
```bash
# preparation data for Linear Programing
python mock_data.py

# Solve the problem
python integer_programming.py
```
When you execute `mock_data.py`, you can see mock data files in `data/toy`.
And executing `integer_programming.py`, also see optimized timetable file in `outputs/toy/`.

## Launch API server with Docker
```bash
cd chronoscheduler/environments

# Create Docker environment
. create_env.sh

# launch api server
docker compose up
```

Check server response:
```bash
# Create Docker environment
curl localhost:8000/test
```

Returns:
```bash
{"message":"Running ChronoScheduler!"}
```

# 📝Note
Only one special type of pre-processing is supported yet...

# 🚀Updates
**2023.06.25**
- Readme update

# Author
kargenk(**gengen**)

# ©License
ChronoScheduler is under [MIT licence](https://en.wikipedia.org/wiki/MIT_License)