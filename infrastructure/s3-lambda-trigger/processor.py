import json
import urllib.parse
import boto3
import time

dynamodb = boto3.resource('dynamodb')
table_name = "S3_File_Audit_Log"
table = dynamodb.Table(table_name)

def handler(event, context):
    print(" Event received from S3!")
    
    for record in event['Records']:
        # Extract event data
        bucket_name = record['s3']['bucket']['name']
        file_name = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']
        event_time = record['eventTime']
        
        print(f"Processing: {file_name} ({size} bytes)")

        #  DynamoDB
        try:
            response = table.put_item(
                Item={
                    'file_name': file_name,     # Primary Key 
                    'bucket': bucket_name,
                    'size_bytes': size,
                    'upload_time': event_time,
                    'status': 'PROCESSED'
                }
            )
            print(f" Saved to DynamoDB: {file_name}")
            
        except Exception as e:
            print(f" Error writing to DynamoDB: {str(e)}")
            raise e # Force Lambda to fail so CloudWatch notify you
        
    return {
        'statusCode': 200,
        'body': json.dumps('File metadata indexed successfully')
    }