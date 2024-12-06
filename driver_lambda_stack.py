from aws_cdk import Stack, Duration, Aws
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_iam import PolicyStatement
from constructs import Construct

class DriverLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, s3_bucket: Bucket, plotting_api_url: str,plotting_api_id: str,**kwargs):
        super().__init__(scope, id, **kwargs)

        self.driver_lambda = Function(
            self, "DriverLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="driver.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),  
            environment={
                'BUCKET_NAME': s3_bucket.bucket_name,
                'PLOTTING_API_URL': plotting_api_url  
            }
        )

        s3_bucket.grant_write(self.driver_lambda)
        
        # Authorize Driver Lambda to invoke API Gateway
        self.driver_lambda.add_to_role_policy(PolicyStatement(
            actions=["execute-api:Invoke"],
            resources=[
                f"arn:aws:execute-api:{Aws.REGION}:{Aws.ACCOUNT_ID}:{plotting_api_id}/prod/*"
            ]
        ))