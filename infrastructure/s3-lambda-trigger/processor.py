import json
import urllib.parse
import boto3
import os

# Security configuration
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.csv', '.json', '.png', '.jpg'}
MAX_SIZE_BYTES = 5 * 1024 * 1024 # 5 MB

dynamodb = boto3.resource('dynamodb')
table_name = "S3_File_Audit_Log"
table = dynamodb.Table(table_name)

def is_safe_file(filename, size):
    # 1. Extension Validation (File Type)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extension {ext} not allowed"
    
    # 2. Size Validation (DoS Protection)
    if size > MAX_SIZE_BYTES:
        return False, f"File too large ({size} bytes)"
        
    return True, "Safe"

def handler(event, context):
    print(" SecOps Lambda starting...")
    
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']
        event_time = record['eventTime']
        
        print(f" Inspecting: {file_name} ({size} bytes)")

        is_safe, reason = is_safe_file(file_name, size)
        
        status = 'PROCESSED' if is_safe else 'BLOCKED'
        
        try:
            item = {
                'file_name': file_name,
                'bucket': bucket_name,
                'size_bytes': size,
                'upload_time': event_time,
                'status': status
            }
            
            if not is_safe:
                item['block_reason'] = reason
                print(f"🚫 BLOCKED: {file_name} - {reason}")
            else:
                print(f" APPROVED: {file_name}")

            table.put_item(Item=item)
            
        except Exception as e:
            print(f"❌ Error writing to DB: {str(e)}")
            raise e
        
    return {
        'statusCode': 200,
        'body': json.dumps('Security scan complete')
    }