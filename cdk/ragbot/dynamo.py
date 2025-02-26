from aws_cdk import (
    Stack,
    aws_dynamodb,
    aws_iam,
    Fn,
)
from constructs import Construct
import json


with open('./config.json') as f:
    config = json.load(f)

app_name = config['name']


class DynamoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        system_table = aws_dynamodb.Table(
            self, f"{app_name}System",
            table_name=f"{app_name.lower()}-system",
            partition_key=aws_dynamodb.Attribute(name='id', type=aws_dynamodb.AttributeType.STRING),
        )
        history_table = aws_dynamodb.Table(
            self, f"{app_name}History",
            table_name=f"{app_name.lower()}-history",
            partition_key=aws_dynamodb.Attribute(name='id', type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name="createdAt", type=aws_dynamodb.AttributeType.NUMBER),
        )

        model_func_role_arn = Fn.import_value(f"{app_name}ModelFuncRoleArn")
        model_func_role = aws_iam.Role.from_role_arn(self, f"{app_name}ModelFuncRole", model_func_role_arn, mutable=True)

        system_table.grant_read_write_data(model_func_role)
        history_table.grant_read_write_data(model_func_role)
