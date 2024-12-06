from aws_cdk import Stack
from aws_cdk.aws_s3 import Bucket, EventType
from aws_cdk.aws_s3_notifications import SnsDestination
from aws_cdk.aws_sns import Topic
from constructs import Construct

class StorageAndNotificationStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create S3 Bucket
        self.s3_bucket = Bucket(self, "Assignment4Bucket")

        # Create SNS Topic
        self.sns_topic = Topic(self, "S3EventTopic")

        # Set up S3 bucket to publish events to the SNS topic
        self.s3_bucket.add_event_notification(EventType.OBJECT_CREATED, SnsDestination(self.sns_topic))
        self.s3_bucket.add_event_notification(EventType.OBJECT_REMOVED, SnsDestination(self.sns_topic))
