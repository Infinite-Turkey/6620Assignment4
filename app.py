from aws_cdk import App
from aws_cdk.aws_s3 import Bucket
from size_tracking_lambda_stack import SizeTrackingLambdaStack
from plotting_lambda_stack import PlottingLambdaStack
from api_stack import ApiGatewayStack
from driver_lambda_stack import DriverLambdaStack
from storage_and_notification_stack import StorageAndNotificationStack
from logging_lambda_stack import LoggingLambdaStack
from constructs import Construct

app = App()

# Create StorageStack to set up S3 bucket
storage_and_notification_stack = StorageAndNotificationStack(app, "StorageAndNotificationStack")

# Create StorageAndTrackingStack to set up DynamoDB and Size Tracking Lambda, passing sns_sqs_stack
size_tracking_lambda_stack = SizeTrackingLambdaStack(app, "SizeTrackingLambdaStack", sns_topic=storage_and_notification_stack.sns_topic, s3_bucket=storage_and_notification_stack.s3_bucket)

# Create PlottingLambdaStack, setting up the Plotting Lambda function
plotting_lambda_stack = PlottingLambdaStack(app, "PlottingLambdaStack",
                                            dynamodb_table=size_tracking_lambda_stack.table,
                                            s3_bucket=storage_and_notification_stack.s3_bucket
                                          )

# Create ApiGatewayStack and integrate it with the Plotting Lambda function
api_gateway_stack = ApiGatewayStack(app, "ApiGatewayStack", plotting_lambda=plotting_lambda_stack.plotting_lambda)

# Create DriverLambdaStack and pass in the API URL and API ID for invocation
driver_lambda_stack = DriverLambdaStack(app, "DriverLambdaStack", 
                                        s3_bucket=storage_and_notification_stack.s3_bucket, 
                                        plotting_api_url=api_gateway_stack.api_url,
                                        plotting_api_id=api_gateway_stack.api_id)

logging_lambda_stack = LoggingLambdaStack(app, "LoggingLambdaStack", sns_topic=storage_and_notification_stack.sns_topic,s3_bucket=storage_and_notification_stack.s3_bucket)


app.synth()
