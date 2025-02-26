from openai import OpenAI
import os
import json

with open('./data/data.json') as f:
    data = json.load(f)

openai_client = OpenAI(api_key=os.environ["OPEN_AI_API_KEY"])

index = []
for title, body in data.items():
    print('title: ' + title)
    print('body: ' + body)

    input = title + '\n' + body

    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=input
    )
    embedding = response.data[0].embedding

    print('embedding: ' + str(embedding))

    index.append({
        'title': title,
        'body': body,
        'embedding': embedding
    })

with open('./data/embed.json', 'w') as f:
    json.dump(index, f)
