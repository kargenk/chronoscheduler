# FROM python:3.11-buster
FROM python:3.11-bullseye

# # 数理最適化ソルバのSCIPをインストール
# RUN apt-get install -y libc6 libgcc-s1 libopenblas0 libstdc++6 libgslcblas0 libtbbmalloc2
# RUN apt-get update && apt-get install /chronoscheduler/solver/SCIPOptSuite-8.0.3-Linux-ubuntu.deb

# Pythonの出力表示をDocker用に調整
ENV PYTHONUNBUFFERED=1

WORKDIR /chronoscheduler

# Poetryで環境を構築
RUN pip install poetry
COPY pyproject.toml* poetry.lock* ./
RUN poetry config virtualenvs.in-project true
RUN if [ -f pyproject.toml ]; then poetry install --no-root; fi

# uvicornのサーバを立ち上げる
ENTRYPOINT ["poetry", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--reload"]