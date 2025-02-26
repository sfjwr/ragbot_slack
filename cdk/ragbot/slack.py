import os

from aws_cdk import (
    aws_iam,
    aws_lambda,
    aws_apigateway,
    aws_logs,
    Duration,
    Stack,
)
from constructs import Construct
import json

with open('./config.json') as f:
    config = json.load(f)

app_name = config['name']


class SlackStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ecr_image = aws_lambda.EcrImageCode.from_asset_image(
            directory=os.path.join(os.getcwd(), "../slack"),
        )

        slack_func_policy_statement = aws_iam.PolicyStatement(actions=[
            "lambda:InvokeFunction",
            "lambda:GetFunction"
        ], resources=["*"])
        slack_func_policy = aws_iam.Policy(self, f"{app_name.lower()}-slack-app-func-policy", statements=[slack_func_policy_statement])

        slack_func_role = aws_iam.Role(
            self, f"{app_name}SlackAppFuncRole",
            role_name=f"{app_name}-slack-app-func-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com")
        )
        slack_func_role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'))
        slack_func_role.attach_inline_policy(slack_func_policy)

        slack_func = aws_lambda.Function(
            self,
            id=f"{app_name.lower()}-slack-app-func",
            code=ecr_image,
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            environment={
                "SLACK_SIGNING_SECRET": os.environ["SLACK_SIGNING_SECRET"],
                "SLACK_OAUTH_TOKEN": os.environ["SLACK_OAUTH_TOKEN"],
            },
            function_name=f"{app_name}SlackApp",
            memory_size=512,
            timeout=Duration.seconds(60),
            architecture=aws_lambda.Architecture.ARM_64,
            role=slack_func_role,
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
        )

        slack_api = aws_apigateway.RestApi(self, f"{app_name.lower()}-slack-app-api")
        resource_app = slack_api.root.add_resource("app")
        resource_app.add_method("POST", aws_apigateway.LambdaIntegration(slack_func))

        aws_logs.LogGroup(self, f"{app_name.lower()}_slack_receive_messages", log_group_name=f"/{app_name.lower()}/slack/message", retention=aws_logs.RetentionDays.INFINITE)
