import json
import urllib.parse

def handler(event, context):
    print("⚡ Event received from S3!")
    
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_name = urllib.parse.unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']
        
        print(f" Bucket: {bucket_name}")
        print(f" File Detected: {file_name}")
        print(f" Size: {size} bytes")
        print(" Processing complete. Ready for the next one.")
        
    return {
        'statusCode': 200,
        'body': json.dumps('File processed successfully')
    }