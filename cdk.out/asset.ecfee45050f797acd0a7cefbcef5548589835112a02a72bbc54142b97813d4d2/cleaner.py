import boto3
import os
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Initialize S3 client
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')

    if not bucket_name:
        raise ValueError("Environment variable 'BUCKET_NAME' must be set")

    print(f"Processing bucket: {bucket_name}")

    # Threshold for total bucket size
    THRESHOLD = 15  # bytes

    try:
        while True:
            # List objects in the bucket
            response = s3.list_objects_v2(Bucket=bucket_name)
            
            if "Contents" not in response or not response["Contents"]:
                print(f"The bucket '{bucket_name}' is empty. No objects to delete.")
                break

            # Calculate total size of the bucket
            total_size = sum(obj["Size"] for obj in response["Contents"])
            print(f"Total bucket size: {total_size} bytes")

            # Check if total size is below the threshold
            if total_size <= THRESHOLD:
                print(f"Bucket size {total_size} is below the threshold of {THRESHOLD}.")
                break

            # Find the largest object in the bucket
            largest_object = max(response["Contents"], key=lambda x: x["Size"])
            largest_key = largest_object["Key"]
            largest_size = largest_object["Size"]

            # Log details of the largest object
            print(f"Largest object to delete: {largest_key}, size: {largest_size} bytes")

            # Delete the largest object
            try:
                s3.delete_object(Bucket=bucket_name, Key=largest_key)
                print(f"Deleted object: {largest_key}, size: {largest_size} bytes")
            except ClientError as e:
                print(f"Failed to delete object '{largest_key}': {e}")
                return {
                    'statusCode': 500,
                    'body': f"Error deleting object: {e}"
                }

        return {
            'statusCode': 200,
            'body': f"Cleaner Lambda executed successfully. Bucket size is now {total_size} bytes."
        }

    except ClientError as e:
        print(f"Error accessing bucket '{bucket_name}': {e}")
        return {
            'statusCode': 500,
            'body': f"Error accessing bucket: {e}"
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'body': f"Unexpected error occurred: {e}"
        }
