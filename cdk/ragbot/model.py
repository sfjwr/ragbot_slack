import os
from aws_cdk import (
    Duration,
    Stack,
    aws_iam,
    aws_lambda,
    aws_logs,
    CfnOutput
)
from constructs import Construct
import json


with open('./config.json') as f:
    config = json.load(f)

app_name = config['name']


class ModelStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        model_func_role = aws_iam.Role(
            self, f"{app_name}ModelFuncRole",
            role_name=f"{app_name.lower()}-model-func-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com")
        )
        model_func_role.add_managed_policy(aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'))
        model_func_role.add_to_policy(aws_iam.PolicyStatement(
            actions=["aoss:APIAccessAll"],
            resources=["*"]
        ))

        ecr_image_model = aws_lambda.EcrImageCode.from_asset_image(
            directory=os.path.join(os.getcwd(), "../model"),
        )
        aws_lambda.Function(
            self,
            id=f"{app_name.lower()}-model",
            code=ecr_image_model,
            handler=aws_lambda.Handler.FROM_IMAGE,
            runtime=aws_lambda.Runtime.FROM_IMAGE,
            environment={
                "OPEN_AI_API_KEY": os.environ["OPEN_AI_API_KEY"]
            },
            function_name=f"{app_name}Model",
            memory_size=512,
            timeout=Duration.seconds(60),
            architecture=aws_lambda.Architecture.ARM_64,
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            role=model_func_role,
        )

        CfnOutput(
            self,
            f"{app_name}ModelFuncRoleArnOutput",
            value=model_func_role.role_arn,
            export_name=f"{app_name}ModelFuncRoleArn"
        )
