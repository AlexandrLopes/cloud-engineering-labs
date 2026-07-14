import argparse
import time
import uuid

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "SecurityAlerts"
REGION = "us-east-1"


def create_table_if_not_exists(dynamodb):
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'alert_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'alert_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            PointInTimeRecoverySpecification={'PointInTimeRecoveryEnabled': True},
        )
        print(f"Creating table {TABLE_NAME}...")
        table.wait_until_exists()
        print(f"Table {TABLE_NAME} created successfully.")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {TABLE_NAME} already exists. Skipping creation.")
            return dynamodb.Table(TABLE_NAME)
        else:
            print(f"Error creating table: {e}")
            raise


def log_alert(table, severity, message, alert_id=None):
    """Logs one security alert. Callable directly by other automation in this
    portfolio (ec2-open-ports, ec2-auto-remediation, s3_security_scanner), not
    just from this script's own CLI."""
    alert_id = alert_id or str(uuid.uuid4())
    timestamp = str(time.time())

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
        print(f"Alert logged: [{severity}] {message}")
    else:
        print(f"Failed to log alert: {message}")

    return alert_id


def main():
    parser = argparse.ArgumentParser(description="Log a security alert to the central DynamoDB table.")
    parser.add_argument("--severity", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], required=True)
    parser.add_argument("--message", required=True, help="Description of the alert")
    args = parser.parse_args()

    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table = create_table_if_not_exists(dynamodb)
    log_alert(table, args.severity, args.message)


if __name__ == "__main__":
    main()
