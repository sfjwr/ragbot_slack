#!/usr/bin/env python3

import aws_cdk as cdk

from ragbot.model import ModelStack
from ragbot.slack import SlackStack
from ragbot.dynamo import DynamoStack

import json

app = cdk.App()
env = {'region': 'ap-northeast-1'}

with open('./config.json') as f:
    config = json.load(f)

ModelStack(app, f"{config['name']}ModelStack", env=env)
DynamoStack(app, f"{config['name']}DynamoStack", env=env)
SlackStack(app, f"{config['name']}SlackStack", env=env)

app.synth()
