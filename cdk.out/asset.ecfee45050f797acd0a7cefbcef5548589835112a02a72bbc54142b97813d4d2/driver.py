import boto3
import time
import urllib3
import os

def lambda_handler(event, context):
    # Initialize boto3 clients
    s3_client = boto3.client('s3')
    bucket_name = os.getenv('BUCKET_NAME')
    api_url = os.getenv('PLOTTING_API_URL')

    # Debugging information
    print(f"Bucket Name: {bucket_name}")
    print(f"Plotting API URL: {api_url}")

    # Function to create an object in the S3 bucket
    def create_object(object_name, content):
        s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=content)
        print(f"Created object: '{object_name}' with content: '{content}'")

    # Function to invoke the plotting API
    def call_plotting_api():
        if not api_url:
            print("Error: The PLOTTING_API_URL environment variable is not configured.")
            return

        http = urllib3.PoolManager()
        response = http.request('POST', api_url)
        print(f"Plotting API called, response status: {response.status}")

    # Perform the required operations
    # Step 1: Create 'assignment1.txt' (19 bytes)
    create_object('assignment1.txt', 'Empty Assignment 1')
    time.sleep(3)  # Wait for potential metric updates or alarms

    # Step 2: Create 'assignment2.txt' (28 bytes)
    create_object('assignment2.txt', 'Empty Assignment 2222222222')
    time.sleep(3)  # Wait for alarms or the Cleaner Lambda to handle 'assignment2.txt'

    # Step 3: Create 'assignment3.txt' (2 bytes)
    create_object('assignment3.txt', '33')
    time.sleep(3)  # Wait for alarms or the Cleaner Lambda to handle 'assignment1.txt'

    # Step 4: Invoke the plotting API
    call_plotting_api()

    return {
        'statusCode': 200,
        'body': 'Driver Lambda executed successfully and invoked the Plotting API.'
    }
