FROM ubuntu:22.04

# タイムゾーンの設定
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 必要なツールのインストール
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    screen \
    vim
# Pythonのダウンロード&インストール
RUN apt apt-get update && apt-get install -y \
    build-essential \
    libncursesw5-dev \
    libbz2-dev \
    libgdbm-dev \
    libc6-dev \
    libsqlite3-dev \
    tk-dev \
    libssl-dev \
    openssl \
    zlib1g-dev \
    libffi-dev
# もしかしたらmake altinstallの方が良いかも(ビルドしなおしたときはaltで実行)
RUN wget --no-check-certificate https://www.python.org/ftp/python/3.11.3/Python-3.11.3.tgz \
    && tar -zxvf Python-3.11.3.tgz \
    && cd Python-3.11.3 \
    && ./configure --enable-optimizations\
    && make -j8 \
    && make install
# そのままだとpoetryの実行時にpythonがないといわれるのでパス回りを解決するパッケージを導入
RUN apt-get update && apt-get install -y python-is-python3

# 数理最適化ソルバのSCIPに必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    m4 \
    xz-utils \
    libgmp-dev \
    unzip \
    zlib1g-dev \
    libboost-program-options-dev \
    libboost-serialization-dev \
    libboost-regex-dev \
    libboost-iostreams-dev \
    libtbb-dev \
    libreadline-dev \
    pkg-config \
    git \
    liblapack-dev \
    libgsl-dev \
    flex \
    bison \
    libcliquer-dev \
    gfortran \
    file \
    dpkg-dev \
    libopenblas-dev \
    rpm
# SOPLEX
RUN cd / \
    && git clone https://github.com/scipopt/soplex.git \
    && mkdir soplex/build \
    && cd soplex/build \
    && cmake .. \
    && make -j8 \
    && make install
# SCIP
RUN cd / \
    && git clone https://github.com/scipopt/scip.git \
    && mkdir scip/build \
    && cd scip/build \
    && cmake .. -DAUTOBUILD=on -DSOPLEX_DIR=/usr/local/bin/soplex \
    && make -j8 \
    && make install

# 不要なものは削除
RUN apt-get autoremove -y

# Pythonの出力表示をDocker用に調整
ENV PYTHONUNBUFFERED=1

WORKDIR /chronoscheduler

# Poetryで環境を構築
RUN pip3 install poetry
COPY pyproject.toml* poetry.lock* ./
RUN poetry config virtualenvs.in-project true
RUN if [ -f pyproject.toml ]; then poetry install --no-root; fi
