discord-messages
===

## dev note

- Discord Application の作成が必要: https://discord.com/developers/applications
- Bot Token も必要。このとき Message Content Intent ON が必要。
- Discord 側で developer mode ON が必要: https://qiita.com/ymzkjpx/items/8f42733d0fb67d454e27

```bash
docker compose up -d --build
docker compose run --rm app pipenv install --dev
docker compose run --rm app pipenv install --dev ruff
docker compose run --rm app pipenv install discord.py
# モジュール入れたら build し直してねー。
```

## How to start

```bash
# 最初のセットアップ
docker compose up -d --build

# Ruff を動かしてみる
docker compose run --rm app pipenv run ruff check .
docker compose run --rm app pipenv run ruff check --fix .

# Python スクリプトを動かしてみる
# NOTE: いやー、このスクリプトは秘密情報多いからここには書けないや。 help コマンドだけここに置いとくよ。
docker compose run --rm app pipenv run python main_001_discord_to_jsonl.py --help
docker compose run --rm app pipenv run python main_002_rawjsonl_to_parsedjsonl.py --help
docker compose run --rm app pipenv run python main_003_parsedjsonl_to_anotherformat.py --help
```

## コミット前確認

```bash
docker compose run --rm app pipenv run ruff check .

# discover: テストを自動探索
# -s tests: テストが入っているディレクトリ
# -v: verbose
docker compose run --rm app pipenv run python -m unittest discover -s tests -v
```
