import json
import boto3
import os

def lambda_handler(event, context):
    # Initialize S3 client
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    
    # Iterate over all records in the event
    for record in event['Records']:
        message_body = json.loads(record['body'])
        sns_message = json.loads(message_body['Message'])
        
        # Extract S3 event details
        s3_event = sns_message['Records'][0]
        bucket_name = s3_event['s3']['bucket']['name']
        object_key = s3_event['s3']['object']['key']
        event_type = s3_event['eventName']
        
        # Determine size delta based on event type
        size_delta = 0
        if event_type.startswith("ObjectCreated"):
            # Get object size for creation events
            size_delta = s3_event['s3']['object'].get('size', 0)  # Defaults to 0 if size is unavailable
        elif event_type.startswith("ObjectRemoved"):
            # Get object size for removal events
            size_delta = -s3_event['s3']['object'].get('size', 0)  # Defaults to 0 if size is unavailable
        
        # Log event details as JSON
        log_data = {
            "object_name": object_key,
            "size_delta": size_delta
        }
        print(json.dumps(log_data, indent=2))
