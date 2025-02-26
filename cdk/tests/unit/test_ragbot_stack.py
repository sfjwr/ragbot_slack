import aws_cdk as core
import aws_cdk.assertions as assertions

from ragbot.model import ModelStack
import json

with open('./config.json') as f:
    config = json.load(f)


# example tests. To run these tests, uncomment this file along with the example
# resource in ragbot/ragbot_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ModelStack(app, f"{config['name']}ModelStack")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
