import json
import urllib.parse
import boto3
import os

# Configurações
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.csv', '.json', '.png', '.jpg'}
MAX_SIZE_BYTES = 5 * 1024 * 1024 # 5 MB
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN'] 

# Inicializa Clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')
table = dynamodb.Table("S3_File_Audit_Log")

def is_safe_file(filename, size):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extension {ext} not allowed"
    if size > MAX_SIZE_BYTES:
        return False, f"File too large ({size} bytes)"
    return True, "Safe"

def send_alert(filename, reason):
    
    subject = f" SECURITY ALERT: Malicious File Blocked!"
    message = f"""
    WARNING: A file was blocked by the Security Lambda.
    
    File Name: {filename}
    Reason: {reason}
    
    Please investigate immediately.
    """
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        print(f" Alert sent to SNS for {filename}")
    except Exception as e:
        print(f" Failed to send SNS alert: {str(e)}")

def handler(event, context):
    print("🛡️ SecOps Lambda starting...")
    
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']
        event_time = record['eventTime']
        
        is_safe, reason = is_safe_file(file_name, size)
        status = 'PROCESSED' if is_safe else 'BLOCKED'
        
        
        if not is_safe:
            print(f" BLOCKED: {file_name} - {reason}")
            send_alert(file_name, reason)
        else:
            print(f" APPROVED: {file_name}")

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
                
            table.put_item(Item=item)
        except Exception as e:
            print(f" Error writing to DB: {str(e)}")
            raise e
            
    return {'statusCode': 200, 'body': json.dumps('Scan complete')}