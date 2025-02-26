# RagBot

SlackでRAGするBotを作成するためのサンプルコード。

ご自由にご利用ください。

# 設定

## configファイル

configファイルに同一のアプリ名を設定する

- `model/config.json`
- `slack/config.json`
- `cdk/config.json`

## 環境変数

以下の環境変数を適切に設定する

- `export OPEN_AI_API_KEY=xxxx`
- `export SLACK_SIGNING_SECRET=xxxx`
- `export SLACK_OAUTH_TOKEN=xxxx`

## データの準備

`data/README.md`に従って`embed.json`を作成し、`model/data/`に置く。

# Deploy

`cdk/README.md`の内容でDeployする

## Slack連携

SlackApi の EventSubscriptions の設定ページでRequestURLを設定する

- `https://xxxx.execute-api.ap-northeast-1.amazonaws.com/prod/app`

その他、SlackApi に必要な権限などは適時設定する
