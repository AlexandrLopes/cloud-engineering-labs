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
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', 'LOCAL_TEST')

ALLOWED_EXTENSIONS = ('.pdf', '.txt', '.csv', '.json')
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def log_blocked_file(file_name, file_size, block_reason):
    """Every blocked file gets an audit record too, not just successful ones."""
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        'file_name': file_name,
        'timestamp': datetime.utcnow().isoformat(),
        'file_size_bytes': file_size,
        'status': 'BLOCKED',
        'block_reason': block_reason
    })


def lambda_handler(event, context):
    try:
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        file_name = record['s3']['object']['key']
        file_size = record['s3']['object']['size']

        print(f"Processing file: {file_name} from bucket: {bucket_name}")

        # Security Validation (Extension Check) — matches the four types this
        # service actually claims to support, not just .csv.
        if not file_name.lower().endswith(ALLOWED_EXTENSIONS):
            reason = f"Unsupported file type: {file_name}"
            print(f"Alert: {reason}. Blocking.")
            log_blocked_file(file_name, file_size, reason)
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=f"SECURITY ALERT: Invalid file type detected ({file_name}).",
                Subject="SECURITY ALERT"
            )
            return {'statusCode': 403, 'body': json.dumps('File blocked: Invalid extension')}

        # DoS Protection (Size Check) — checked against the S3 event metadata,
        # before ever downloading the file, so an oversized upload doesn't even
        # cost a download.
        if file_size > MAX_FILE_SIZE_BYTES:
            reason = f"File exceeds size limit: {file_size} bytes (max {MAX_FILE_SIZE_BYTES})"
            print(f"Alert: {reason}. Blocking.")
            log_blocked_file(file_name, file_size, reason)
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=f"SECURITY ALERT: Oversized file blocked ({file_name}, {file_size} bytes).",
                Subject="SECURITY ALERT"
            )
            return {'statusCode': 403, 'body': json.dumps('File blocked: Exceeds size limit')}

        download_path = f"/tmp/{uuid.uuid4()}_{os.path.basename(file_name)}"
        s3_client.download_file(bucket_name, file_name, download_path)

        # CSV gets the numeric analysis; other allowed types (.pdf, .txt, .json)
        # are audited and stored, but there's no "amount" column to total.
        total_amount = 0.0
        row_count = 0

        if file_name.lower().endswith('.csv'):
            with open(download_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if 'amount' in row:
                        total_amount += float(row['amount'])
                        row_count += 1
            print(f"Analysis Complete: {row_count} rows processed. Total value: ${total_amount}")
        else:
            print(f"File type {file_name} accepted and audited (no numeric analysis for this type).")

        os.remove(download_path)

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
