from aws_cdk import Stack, Duration
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType, BillingMode
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct
from aws_cdk.aws_sqs import Queue
from aws_cdk.aws_sns import Topic
from aws_cdk.aws_sns_subscriptions import SqsSubscription
from aws_cdk.aws_s3 import Bucket

class SizeTrackingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, sns_topic: Topic, s3_bucket:Bucket, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create DynamoDB Table
        self.table = Table(self, "TrackingTable",
            partition_key=Attribute(name="BucketName", type=AttributeType.STRING),
            sort_key=Attribute(name="Timestamp", type=AttributeType.NUMBER),
            billing_mode=BillingMode.PAY_PER_REQUEST
        )

        # Create SQS Queue and subscribe it to the SNS topic
        self.sqs_queue = Queue(self, "S3EventQueue", visibility_timeout=Duration.seconds(300))
        sns_topic.add_subscription(SqsSubscription(self.sqs_queue))

        # Create Size Tracking Lambda
        self.size_tracking_lambda = Function(
            self, "SizeTrackingLambda",
            runtime=Runtime.PYTHON_3_8,
            handler="size.lambda_handler",
            timeout=Duration.seconds(300),
            code=Code.from_asset("lambda"),
            environment={
                'DYNAMODB_TABLE_NAME': self.table.table_name,
                'BUCKET_NAME': s3_bucket.bucket_name
            }
        )

        # Set up SQS queue as event source for the Lambda
        self.size_tracking_lambda.add_event_source(SqsEventSource(self.sqs_queue))


        # Grant Lambda permissions to access DynamoDB
        self.table.grant_read_write_data(self.size_tracking_lambda)

        # Grant Lambda permissions to access SNS
        sns_topic.grant_publish(self.size_tracking_lambda)

        # Grant Lambda permissions to access S3
        s3_bucket.grant_read(self.size_tracking_lambda)
        
        # Grant Lambda permissions to access SQS
        self.sqs_queue.grant_consume_messages(self.size_tracking_lambda)