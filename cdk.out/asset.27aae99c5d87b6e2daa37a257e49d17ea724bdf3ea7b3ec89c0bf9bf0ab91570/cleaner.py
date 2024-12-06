import boto3
import os

def lambda_handler(event, context):
    # Create an S3 client
    s3 = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    print(f"Processing bucket: {bucket_name}")
    
    # List objects in the specified bucket
    response = s3.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        # Find the object with the largest size
        largest_object = max(response["Contents"], key=lambda x: x["Size"])
        largest_key = largest_object["Key"]
        
        # Log details of the largest object
        print(f"Largest object: {largest_key}, size: {largest_object['Size']} bytes")
        
        # Delete the largest object
        s3.delete_object(Bucket=bucket_name, Key=largest_key)
        print(f"Deleted: {largest_key}, size: {largest_object['Size']} bytes")
    else:
        print("No objects found in the bucket.")
