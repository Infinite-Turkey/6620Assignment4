import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Initialize S3 client
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')

    # Check if BUCKET_NAME is set
    if not bucket_name:
        print("Error: Environment variable 'BUCKET_NAME' is not set.")
        return {
            'statusCode': 400,
            'body': "Environment variable 'BUCKET_NAME' is not set."
        }

    print(f"Processing bucket: {bucket_name}")
    print("Received event:", event)

    try:
        # List objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        if "Contents" not in response or not response["Contents"]:
            print(f"The bucket '{bucket_name}' is empty. No objects to delete.")
            return {
                'statusCode': 200,
                'body': f"The bucket '{bucket_name}' is empty. No action taken."
            }

        # Find the largest object in the bucket
        largest_object = max(response["Contents"], key=lambda x: x["Size"])
        largest_key = largest_object["Key"]

        # Log details of the largest object
        print(f"Largest object: {largest_key}, size: {largest_object['Size']} bytes")

        # Delete the largest object
        try:
            s3.delete_object(Bucket=bucket_name, Key=largest_key)
            print(f"Successfully deleted: {largest_key}, size: {largest_object['Size']} bytes")
            return {
                'statusCode': 200,
                'body': f"Deleted largest object: {largest_key} ({largest_object['Size']} bytes)."
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            print(f"Error deleting object '{largest_key}' from bucket '{bucket_name}': {error_code}")
            return {
                'statusCode': 500,
                'body': f"Failed to delete object '{largest_key}': {error_code}."
            }

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        print(f"Error listing objects in bucket '{bucket_name}': {error_code}")
        return {
            'statusCode': 500,
            'body': f"Failed to list objects in bucket '{bucket_name}': {error_code}."
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Unexpected error occurred: {str(e)}"
        }
