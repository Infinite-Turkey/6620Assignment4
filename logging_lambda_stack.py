from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_sqs as sqs,
    aws_cloudwatch as cloudwatch,
)
import aws_cdk.aws_cloudwatch_actions as actions
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from aws_cdk.aws_sqs import Queue
from aws_cdk.aws_sns import Topic
from aws_cdk.aws_sns_subscriptions import SqsSubscription
from aws_cdk.aws_s3 import Bucket
from constructs import Construct
import aws_cdk.aws_lambda as lambda_
from aws_cdk.aws_sns_subscriptions import LambdaSubscription

class LoggingLambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, sns_topic: Topic, s3_bucket: Bucket, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create SQS Queue and subscribe it to the SNS topic
        self.sqs_queue = Queue(self, "S3EventQueue", visibility_timeout=Duration.seconds(300))
        sns_topic.add_subscription(SqsSubscription(self.sqs_queue))

        # Create Logging Lambda
        self.logging_lambda = _lambda.Function(
            self, "LoggingLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="logging.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            environment={
                'BUCKET_NAME': s3_bucket.bucket_name
            }
        )
        s3_bucket.grant_read_write(self.logging_lambda)

        # Set up SQS event source for the Logging Lambda
        self.logging_lambda.add_event_source(SqsEventSource(self.sqs_queue))

        # Create a Log Group for the Logging Lambda
        log_group = logs.LogGroup(self, "LoggingLambdaLogGroup",
                                  log_group_name=f"/aws/lambda/{self.logging_lambda.function_name}",
                                  retention=logs.RetentionDays.ONE_WEEK)

        # Add Metric Filter to extract size_delta from logs
        metric_filter = logs.MetricFilter(
            self, "SizeDeltaMetricFilter",
            log_group=log_group,
            metric_namespace="Assignment4App",
            metric_name="TotalObjectSize",
            filter_pattern=logs.FilterPattern.exists("$.size_delta"),  # Ensure the field exists
            metric_value="$.size_delta"
        )

        # Initialize the Cleaner Lambda
        self.cleaner_lambda = _lambda.Function(
            self, "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="cleaner.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            environment={
                'BUCKET_NAME': s3_bucket.bucket_name
            }
        )
        
        s3_bucket.grant_read_write(self.cleaner_lambda)
        s3_bucket.grant_delete(self.cleaner_lambda)

        # Create an SNS topic specifically for triggering the CleanerLambda
        alarm_topic = Topic(self, "AlarmTopic")

        # Subscribe the CleanerLambda to the SNS topic
        alarm_topic.add_subscription(LambdaSubscription(self.cleaner_lambda))

        # Create CloudWatch Alarm based on the TotalObjectSize metric
        self.size_threshold_alarm = cloudwatch.Alarm(
            self, "SizeThresholdAlarm",
            metric=cloudwatch.Metric(
                namespace="Assignment4App",
                metric_name="TotalObjectSize",
                statistic="Sum",
                period=Duration.seconds(10),  
            ),
            threshold=15,
            evaluation_periods=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING  # Ignore missing data for immediate triggering
        )

        # Add Cleaner Lambda as an action to the alarm using custom action
        self.size_threshold_alarm.add_alarm_action(
            actions.SnsAction(alarm_topic)
        )