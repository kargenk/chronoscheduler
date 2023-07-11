# dockerイメージのビルド
docker build ./ --tag $(whoami)_scip:latest

# dockerコンテナの立ち上げ
docker run --name kg_scip \
    -v /home/$(whoami)/chronoscheduler:/chronoscheduler \
    -it -d --shm-size=32gb $(whoami)_scip:latest /bin/bash