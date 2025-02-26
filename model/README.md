# 環境設定

1. `$ python -m venv .venv`
1. `$ source .venv/bin/activate`
1. `$ pip install pipenv`
1. `$ pipenv install`

## 環境変数にキーを設定する

export OPEN_AI_API_KEY=xxxx

## データの準備

`data/embed.json`にデータを設置する

# ローカルでの実行

1. `$ aws configure`
1. `$ source .venv/bin/activate`
1. `$ python app.py`
