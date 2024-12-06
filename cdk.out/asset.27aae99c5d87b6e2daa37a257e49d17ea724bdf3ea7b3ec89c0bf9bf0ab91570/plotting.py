import boto3
import os
import matplotlib.pyplot as plt
import io
import time
import datetime
import matplotlib.dates as mdates

# Set MPLCONFIGDIR to /tmp to handle matplotlib cache in AWS Lambda
os.environ['MPLCONFIGDIR'] = '/tmp'

# Initialize AWS resources and environment variables
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
table_name = os.getenv('DYNAMODB_TABLE_NAME')
bucket_name = os.getenv('BUCKET_NAME')
plot_bucket_name = os.getenv('PLOT_BUCKET_NAME')

def query_size_history():
    """
    Query the DynamoDB table for bucket size changes in the last 10 seconds.
    """
    table = dynamodb.Table(table_name)
    now = int(time.time())
    ten_seconds_ago = now - 10
    
    print(f"Querying for size history between {ten_seconds_ago} and {now} for bucket: {bucket_name}")
    
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name) & 
                               boto3.dynamodb.conditions.Key('Timestamp').between(ten_seconds_ago, now)
    )
    return response['Items']

def get_max_size():
    """
    Retrieve the maximum bucket size recorded in the DynamoDB table.
    """
    table = dynamodb.Table(table_name)
    print(f"Scanning table {table_name} for max size of bucket: {bucket_name}")
    
    response = table.scan(
        ProjectionExpression='TotalSize',
        FilterExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name)
    )
    
    if not response['Items']:
        print("No size data found in the table.")
        return 0
    
    max_size = max(int(item['TotalSize']) for item in response['Items'])
    print(f"Max bucket size recorded: {max_size} bytes")
    return max_size

def plot_size_history(size_data, max_size):
    """
    Generate a plot of bucket size changes over time.
    """
    timestamps = [datetime.datetime.fromtimestamp(item['Timestamp']) for item in size_data]
    sizes = [int(item['TotalSize']) for item in size_data]
    
    print("Generating size history plot...")
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, sizes, label='Bucket Size (last 10s)', marker='o')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator())
    plt.axhline(y=max_size, color='r', linestyle='--', label=f'Max Size: {max_size} bytes')
    plt.title('Bucket Size Changes (Last 10 Seconds)')
    plt.xlabel('Time')
    plt.ylabel('Size (Bytes)')
    plt.legend()
    plt.gcf().autofmt_xdate()

    # Save plot to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    print("Plot generated successfully.")
    
    return buf

def upload_plot_to_s3(buf):
    """
    Upload the generated plot to the specified S3 bucket.
    """
    plot_key = 'plot.png'
    print(f"Uploading plot to S3 bucket: {plot_bucket_name} with key: {plot_key}")
    s3_client.put_object(Bucket=plot_bucket_name, Key=plot_key, Body=buf, ContentType='image/png')
    print("Plot uploaded successfully.")

def lambda_handler(event, context):
    """
    Lambda function entry point to query size history, plot data, and upload the plot to S3.
    """
    size_data = query_size_history()
    max_size = get_max_size()
    
    plot_buffer = plot_size_history(size_data, max_size)
    upload_plot_to_s3(plot_buffer)
    
    return {
        'statusCode': 200,
        'body': "Plot successfully generated and uploaded to S3 as plot.png."
    }
