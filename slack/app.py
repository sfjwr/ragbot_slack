import os
import re
import time
import json
import boto3
import hashlib
import datetime

from botocore.config import Config
from slack_bolt import App, Ack
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

task_root = os.environ.get("LAMBDA_TASK_ROOT", '.')
with open(os.path.join(task_root, "config.json")) as f:
    config = json.load(f)

app_name = config['name']

conv_log_group_name = f"/{app_name.lower()}/slack/message"
conv_log_stream_name = f'{int(time.time())}'

logs = boto3.Session().client('logs')
logs.create_log_stream(logGroupName=conv_log_group_name,
                       logStreamName=conv_log_stream_name)


app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    token=os.environ["SLACK_OAUTH_TOKEN"],
    process_before_response=True,
)


def put_conv_log(message):
    print(message)
    logs.put_log_events(
        logGroupName=conv_log_group_name,
        logStreamName=conv_log_stream_name,
        logEvents=[{
            'timestamp': int(time.time()) * 1000,
            'message': message
        }])


def invoke_model(session_id, text):
    conf = Config(read_timeout=60)
    client = boto3.client("lambda", config=conf)

    response = client.invoke(
        FunctionName=f"{app_name}Model",
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'session_id': session_id,
            'body': text,
        })
    )

    payload = json.loads(response['Payload'].read())

    return payload['response']


def process_message(event, say):
    if event.get('subtype') == 'bot_message':
        # 自分からのメッセージは無視(無限ループ対策)
        return

    input_text = event['text']

    # メンションとオプション指定を削除
    input_text = re.sub('^\\s*(<.+>)?\\s*(\\[.+\\]\\s*)?', '', input_text)

    put_conv_log(f'Q: {input_text}')

    # セッションIDを生成
    channel = event.get('channel') or 'channel'  # チャンネル毎にセッションを変える
    thread = event.get('thread_ts') or 'thread_ts'  # スレッド毎にセッションを変える
    date = str(datetime.date.today())  # 日付が変わるとセッションを変える
    session_id = hashlib.md5(f'{channel}_{thread}_{date}'.encode()).hexdigest()

    # モデル呼び出し
    output_text = invoke_model(session_id, input_text)

    if type(output_text) == list:
        output_text = '\n'.join(output_text)

    put_conv_log(f'A: {output_text}')

    say(text=output_text, thread_ts=event.get("thread_ts"))


def receive_mention(_, event, say):
    try:
        process_message(event, say)
    except Exception as e:
        message = str(e)
        print(message)
        say(text=message, thread_ts=event.get("thread_ts"))


def receive_message(_, event, say):
    try:
        if 'channel_type' not in event or event['channel_type'] != 'im':
            # DirectMessage以外は無視
            return

        process_message(event, say)

    except Exception as e:
        message = str(e)
        print(message)
        say(text=message, thread_ts=event.get("thread_ts"))


def receive_command(command, say):
    try:
        text = command['text']
        args = text.split(' ')
        if args[0] == '':
            # 今のところコマンドは無し
            pass
        else:
            say('コマンドが見つかりませんでした。')
            return
    except Exception as e:
        message = str(e)
        print(message)
        say(message)


def just_ack(ack: Ack):
    ack()


app.event("app_mention")(
    ack=just_ack,
    lazy=[receive_mention]
)

app.event("message")(
    ack=just_ack,
    lazy=[receive_message]
)

app.command(f"/{app_name.lower()}")(
    ack=just_ack,
    lazy=[receive_command]
)


def handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
