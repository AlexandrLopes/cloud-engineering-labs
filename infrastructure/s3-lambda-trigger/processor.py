import json
import boto3
import csv
import os
import uuid
from datetime import datetime

# AWS Clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

# Environment Variables
TABLE_NAME = "S3_File_Audit_Log"
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    try:
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']
        file_size = record['s3']['object']['size']
        
        print(f"Processing file: {file_name} from bucket: {bucket_name}")

        # Security Validation (Extension Check)
        if not file_name.endswith('.csv'):
            print("Alert: Unsupported file type. Blocking.")
            msg = f"SECURITY ALERT: Invalid file type detected ({file_name})."
            sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=msg, Subject="SECURITY ALERT")
            return {
                'statusCode': 403,
                'body': json.dumps('File blocked: Invalid extension')
            }

        download_path = f"/tmp/{uuid.uuid4()}_{file_name}"
        s3_client.download_file(bucket_name, file_name, download_path)

        total_amount = 0.0
        row_count = 0
        
        with open(download_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'amount' in row:
                    total_amount += float(row['amount'])
                    row_count += 1
        
        print(f"Analysis Complete: {row_count} rows processed. Total value: ${total_amount}")

        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            'file_name': file_name,
            'timestamp': datetime.utcnow().isoformat(),
            'file_size_bytes': file_size,
            'status': 'PROCESSED',
            'total_value': str(total_amount), 
            'records_count': row_count
        })

        return {
            'statusCode': 200,
            'body': json.dumps(f"Success! Total processed: {total_amount}")
        }

    except Exception as e:
        print(f"Critical Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Internal Server Error')}