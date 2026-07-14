import time
import uuid

import boto3
from botocore.exceptions import ClientError

ALERTS_TABLE_NAME = "SecurityAlerts"
ALERTS_REGION = "us-east-1"


def log_alert(severity, message):
    """Writes a finding to the shared SecurityAlerts table (see
    dynamodb-security-log in this portfolio). The table is provisioned by
    that project, not created here — if it doesn't exist yet, this logs a
    warning and the audit continues normally."""
    try:
        table = boto3.resource('dynamodb', region_name=ALERTS_REGION).Table(ALERTS_TABLE_NAME)
        table.put_item(Item={
            'alert_id': str(uuid.uuid4()),
            'timestamp': str(time.time()),
            'severity': severity,
            'message': message,
            'status': 'OPEN',
            'source': 's3_security_scanner',
        })
    except ClientError as e:
        print(f"  (Could not write to SecurityAlerts table: {e.response['Error']['Code']})")


def audit_bucket(s3_client, bucket_name):
    """Checks a single bucket for missing encryption and public exposure."""
    result = {"name": bucket_name, "encrypted": False, "public": None, "error": None}

    # Encryption check
    try:
        s3_client.get_bucket_encryption(Bucket=bucket_name)
        result["encrypted"] = True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
            result["encrypted"] = False
        else:
            result["error"] = str(e)
            return result

    # Public access check
    try:
        pab = s3_client.get_public_access_block(Bucket=bucket_name)["PublicAccessBlockConfiguration"]
        fully_blocked = all([
            pab.get("BlockPublicAcls", False),
            pab.get("BlockPublicPolicy", False),
            pab.get("IgnorePublicAcls", False),
            pab.get("RestrictPublicBuckets", False),
        ])
        result["public"] = not fully_blocked
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
            result["public"] = True
        else:
            result["error"] = str(e)

    return result


def generate_report():
    s3 = boto3.client("s3")
    print("--- STARTING S3 SECURITY AUDIT ---\n")

    buckets = s3.list_buckets()["Buckets"]
    vulnerable_count = 0

    for bucket in buckets:
        name = bucket["Name"]
        audit = audit_bucket(s3, name)

        if audit["error"]:
            print(f"[  ERROR] Could not fully audit '{name}': {audit['error']}")
            continue

        is_public = audit["public"]
        is_encrypted = audit["encrypted"]

        if is_public and not is_encrypted:
            print(f"[CRITICAL] '{name}' is PUBLIC and NOT ENCRYPTED!")
            vulnerable_count += 1
            log_alert("CRITICAL", f"Bucket '{name}' is public and not encrypted")
        elif not is_encrypted:
            print(f"[ALERT] '{name}' is NOT ENCRYPTED.")
            vulnerable_count += 1
            log_alert("HIGH", f"Bucket '{name}' is not encrypted")
        elif is_public:
            print(f"[ALERT] '{name}' is PUBLIC (encrypted, but still exposed).")
            vulnerable_count += 1
            log_alert("MEDIUM", f"Bucket '{name}' is public despite encryption")
        else:
            print(f"[ OK] '{name}' is encrypted and not public.")

    print(f"\n--- SUMMARY: {vulnerable_count} vulnerable buckets found (out of {len(buckets)}). ---")


if __name__ == "__main__":
    generate_report()
