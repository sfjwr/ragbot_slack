import os
import json
from openai import OpenAI
from datetime import datetime, timezone
import uuid
import decimal
import boto3
from boto3.dynamodb.conditions import Key
from zoneinfo import ZoneInfo
from numpy import dot
from numpy.linalg import norm

default_prompt_system = '''
ユーザーの質問に対する回答を作成してください。

回答に必要であれば、以下のinformationを参照してください。
informationに示す文章には、0から1の範囲の数値が、ユーザーの発言に対する類似度として付与されています。類似度は1が最もユーザーの発言に近いという意味です。

# information

{information}

# その他の情報

- 現在日時: {datetime}
'''

task_root = os.environ.get("LAMBDA_TASK_ROOT", '.')
with open(os.path.join(task_root, "config.json")) as f:
    config = json.load(f)

app_name = config['name']

openai_client = OpenAI(api_key=os.environ["OPEN_AI_API_KEY"])

table_system = boto3.resource('dynamodb').Table(f"{app_name.lower()}-system")
table_history = boto3.resource('dynamodb').Table(f"{app_name.lower()}-history")


with open('./data/embed.json') as f:
    index = json.load(f)


def embed(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))


def search(vec, k=5):
    results = map(
        lambda i: {
            'title': i['title'],
            'body': i['body'],
            'similarity': cosine_similarity(i['embedding'], vec)
        },
        index
    )
    results = sorted(results, key=lambda i: i['similarity'], reverse=True)

    return results[:k]


def get_system(id):
    items = table_system.query(KeyConditionExpression=Key('id').eq(id))['Items']

    if len(items) == 0:
        return None

    return items[0]


def get_history(session_id):
    items = table_history.query(
        KeyConditionExpression=Key('id').eq(session_id),
        ScanIndexForward=False,
        Limit=10
    )["Items"]
    return items[::-1]


def add_history(session_id, role, content):
    data = {
        'id': session_id,
        'messageId': str(uuid.uuid1()),
        'role': role,
        'content': content,
        'createdAt': decimal.Decimal(datetime.now(timezone.utc).timestamp()),
    }

    table_history.put_item(
        Item=data
    )


def handler(event, context):
    try:
        session_id = event['session_id']
        user_content = event['body']

        # 会話履歴取得
        histories = get_history(session_id)
        histories = list(map(lambda h: {'role': h['role'], 'content': h['content']}, histories))

        # 情報検索
        vec = embed(user_content)
        info = search(vec)
        information = '\n\n'.join(map(lambda e: f"## 類似度 {e['similarity']}\n{e['body']}", info)).replace('\\n', '\n')
        info_title = '\n'.join(map(lambda e: f"- {e['title']}({e['similarity']})", info))

        # プロンプト取得
        prompt = get_system('prompt')
        now_jst = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S (%A)")
        prompt_system = (default_prompt_system if prompt is None else prompt['system']).format(
            datetime=now_jst,
            information=information,
        ).strip()

        # 発言生成
        response = openai_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt_system,
                }
            ] + histories + [
                {
                    "role": "user",
                    "content": user_content,
                }
            ],
            model="gpt-4o",
            n=1,
            temperature=1.0,
            frequency_penalty=0.5,
        )
        assistant_content = response.choices[0].message.content

        # 履歴保存
        add_history(session_id, 'user', user_content)
        add_history(session_id, 'assistant', assistant_content)

        result = assistant_content + '\n\n---\n' + info_title

    except Exception as e:
        print(e)
        result = str(e)

    return {'response': result}


if __name__ == "__main__":
    result = handler({'session_id': 'test_session', 'body': '皇位は世襲ですか？'}, {})
    print(result)
