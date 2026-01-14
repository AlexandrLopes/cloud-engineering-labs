import boto3
import time
from botocore.exceptions import ClientError

TABLE_NAME = "SecurityAlerts"
REGION = "us-east-1"

def create_table_if_not_exists(dynamodb):
    
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'alert_id', 'KeyType': 'HASH'},  # Partition Key
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'} # Sort Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'alert_id', 'AttributeType': 'S'}, # S = String
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f" Creating table {TABLE_NAME}... (This might take 10 seconds)")
        table.wait_until_exists() # The script will remain here until AWS finishes creating it.
        print(f" Table {TABLE_NAME} created successfully!")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"  Table {TABLE_NAME} already exists. Skipping creation.")
            return dynamodb.Table(TABLE_NAME)
        else:
            print(f"❌ Error creating table: {e}")
            raise

def log_alert(table, alert_id, severity, message):
    """
    Log security
    """
    timestamp = str(time.time())
    
    print(f" Logging alert: {alert_id}...")
    
    response = table.put_item(
        Item={
            'alert_id': alert_id,
            'timestamp': timestamp,
            'severity': severity,
            'message': message,
            'status': 'OPEN'
        }
    )
    
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("✅ Alert logged successfully!")
    else:
        print("❌ Failed to log alert.")

def main():
    # Connects to DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    # 1. Checks the table
    table = create_table_if_not_exists(dynamodb)
    
    # 2. Entering false data for testing purposes
    log_alert(table, "ALERT-001", "HIGH", "Port 22 Open to World (0.0.0.0/0)")
    log_alert(table, "ALERT-002", "MEDIUM", "S3 Bucket Publicly Accessible")

if __name__ == "__main__":
    main()