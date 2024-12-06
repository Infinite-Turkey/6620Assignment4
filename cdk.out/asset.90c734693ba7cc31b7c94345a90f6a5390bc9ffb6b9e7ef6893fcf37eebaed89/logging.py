import json
import boto3
import os

# Initialize AWS clients
logs_client = boto3.client('logs')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Ensure required environment variables are set
    bucket_name = os.getenv('BUCKET_NAME')
    log_group_name = os.getenv('LOG_GROUP_NAME')
    if not bucket_name or not log_group_name:
        raise ValueError("Environment variables BUCKET_NAME and LOG_GROUP_NAME must be set.")

    for record in event['Records']:
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
            size_delta = -query_object_size(log_group_name, object_key)

        # Log the event details
        log_data = {
            "object_name": object_key,
            "size_delta": size_delta,
            "event_type": event_type
        }
        print(json.dumps(log_data, indent=2))


def query_object_size(log_group_name, object_key):
    """
    Query CloudWatch Logs to find the size of the object that was deleted.
    """
    query = f'{{ $.object_name = "{object_key}" }}'
    print(f"Querying CloudWatch Logs for object: {object_key}")

    try:
        response = logs_client.filter_log_events(
            logGroupName=log_group_name,
            filterPattern=query
        )
        for event in response.get('events', []):
            log_message = json.loads(event['message'])
            size_delta = log_message.get('size_delta', 0)
            print(f"Found size_delta for {object_key}: {size_delta}")
            return size_delta  # Return the size of the object
    except Exception as e:
        print(f"Error querying CloudWatch Logs: {str(e)}")

    # Return 0 if size cannot be found
    return 0
