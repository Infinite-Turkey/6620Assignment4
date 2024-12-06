import json
import boto3
import os
import time

# Initialize AWS clients
logs_client = boto3.client('logs')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = os.getenv('BUCKET_NAME')
    if not bucket_name:
        raise ValueError("Environment variable BUCKET_NAME is not set")

    for record in event['Records']:
        try:
            # Parse the SQS message
            message_body = json.loads(record['body'])
            sns_message = json.loads(message_body['Message'])
            s3_event = sns_message['Records'][0]

            object_key = s3_event['s3']['object']['key']
            event_type = s3_event['eventName']
            size_delta = 0

            if event_type.startswith("ObjectCreated"):
                # Get size directly for created events
                size_delta = s3_event['s3']['object'].get('size', 0)
            elif event_type.startswith("ObjectRemoved"):
                # Query CloudWatch Logs to find object size
                size_delta = -query_object_size(object_key)

            # Log the event details
            log_data = {
                "event_type": event_type,
                "object_name": object_key,
                "size_delta": size_delta
            }
            print(json.dumps(log_data, indent=2))
        except Exception as e:
            print(f"Error processing record: {record}")
            print(f"Exception: {e}")


def query_object_size(object_key):
    """
    Query CloudWatch Logs to find the size of the deleted object.
    """
    log_group_name = os.getenv('LOG_GROUP_NAME')
    if not log_group_name:
        print("LOG_GROUP_NAME environment variable is not set")
        return 0

    try:
        # Restrict time range to the last 10 minutes
        end_time = int(time.time() * 1000)
        start_time = end_time - (10 * 60 * 1000)  # Last 10 minutes in milliseconds

        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            filterPattern=f'"{object_key}"',  # Match logs containing the object_key
            startTime=start_time,
            endTime=end_time
        )

        for event in response.get('events', []):
            log_message = json.loads(event['message'])
            if log_message.get("object_name") == object_key:
                return log_message.get("size_delta", 0)  # Return the size of the object

        print(f"No matching logs found for object: {object_key}")
        return 0
    except Exception as e:
        print(f"Error querying CloudWatch Logs for object {object_key}: {e}")
        return 0
