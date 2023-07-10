# Dockerイメージのビルド
docker compose build

# # Poetryに依存ライブラリを追加(初回のみ)
# docker compose run \
#     --entrypoint "poetry init \
#         --name chronoscheduler-front \
#         --dependency fastapi \
#         --dependency uvicorn[standard]" \
#     chronoscheduler-front

# # Poetryで依存ライブラリをインストール
# docker compose run \
#     --entrypoint "poetry install --no-root" chronoscheduler-front

# # Poetryで依存ライブラリを追加でインストールするとき
# docker compose run \
#     --entrypoint "poetry add streamlit" chronoscheduler-front

# # 新しい依存ライブラリを追加したときは再ビルド
# docker compose build --no-cache