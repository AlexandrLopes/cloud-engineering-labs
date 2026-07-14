import boto3
from botocore.exceptions import ClientError


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

    # Public access check — the field the mocked version collected but never
    # actually evaluated.
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
            # No block configuration at all — nothing is actively preventing
            # public access, so this is treated as a potential exposure,
            # not silently skipped.
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
            print(f"[⚠️  ERROR] Could not fully audit '{name}': {audit['error']}")
            continue

        is_public = audit["public"]
        is_encrypted = audit["encrypted"]

        if is_public and not is_encrypted:
            print(f"[❌ CRITICAL] '{name}' is PUBLIC and NOT ENCRYPTED!")
            vulnerable_count += 1
        elif not is_encrypted:
            print(f"[⚠️  ALERT] '{name}' is NOT ENCRYPTED.")
            vulnerable_count += 1
        elif is_public:
            print(f"[⚠️  ALERT] '{name}' is PUBLIC (encrypted, but still exposed).")
            vulnerable_count += 1
        else:
            print(f"[✅ OK] '{name}' is encrypted and not public.")

    print(f"\n--- SUMMARY: {vulnerable_count} vulnerable buckets found (out of {len(buckets)}). ---")


if __name__ == "__main__":
    generate_report()
