import boto3
import os
import matplotlib.pyplot as plt
import io
import datetime
import time
import matplotlib.dates as mdates

# Set MPLCONFIGDIR to /tmp to avoid matplotlib cache issues in Lambda
os.environ['MPLCONFIGDIR'] = '/tmp'

def lambda_handler(event, context):
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    bucket_name = os.getenv('PLOT_BUCKET_NAME')

    if not table_name or not bucket_name:
        raise ValueError("Environment variables 'DYNAMODB_TABLE_NAME' and 'PLOT_BUCKET_NAME' must be set.")

    # Query the size history from DynamoDB
    table = dynamodb.Table(table_name)
    end_time = int(time.time())
    start_time = end_time - 60  # Look at the last 60 seconds
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('BucketName').eq(bucket_name) &
                               boto3.dynamodb.conditions.Key('Timestamp').between(start_time, end_time)
    )
    size_data = response.get('Items', [])

    if not size_data:
        print("No size data found for the last 60 seconds.")
        return {
            'statusCode': 200,
            'body': "No data to plot."
        }

    # Extract timestamps and sizes
    timestamps = [datetime.datetime.fromtimestamp(item['Timestamp']) for item in size_data]
    sizes = [int(item['TotalSize']) for item in size_data]

    # Log the data
    print(f"Timestamps: {timestamps}")
    print(f"Sizes: {sizes}")

    # Generate the plot
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, sizes, marker='o', label='Bucket Size')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.SecondLocator(interval=10))  # Adjust interval for readability
    plt.grid(True)
    plt.title("Bucket Size Over Last 60 Seconds")
    plt.xlabel("Time")
    plt.ylabel("Size (Bytes)")
    plt.legend()
    plt.gcf().autofmt_xdate()

    # Save plot to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Upload the plot to S3
    plot_key = "plot.png"
    s3.put_object(Bucket=bucket_name, Key=plot_key, Body=buf, ContentType='image/png')

    print(f"Plot saved to S3 bucket '{bucket_name}' as '{plot_key}'.")
    return {
        'statusCode': 200,
        'body': f"Plot successfully generated and uploaded to S3 as {plot_key}."
    }
