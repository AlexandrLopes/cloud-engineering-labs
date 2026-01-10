import datetime

# --- MOCK DATA (Simulating AWS API response) ---
aws_s3_buckets = [
    {"Name": "financial-sensitive-data", "Encryption": "AES256", "Public": False},
    {"Name": "static-site-images", "Encryption": "None", "Public": True},
    {"Name": "app-logs-prod", "Encryption": "AWS-KMS", "Public": False},
    {"Name": "legacy-backup-dev", "Encryption": "None", "Public": False},
    # Added a 'broken' bucket (missing encryption key) to test script resilience
    {"Name": "ghost-bucket-legacy", "Public": True} 
]

def audit_bucket(bucket_data):
    
    # Using .get() prevents a crash if the 'Encryption' key is missing.
    # It defaults to 'None' if the key is not found.
    
    encryption_status = bucket_data.get('Encryption', 'None')
    
    if encryption_status == "None":
        return False  
    else:
        return True   

def generate_report():
    
    print(f"--- STARTING S3 SECURITY AUDIT [{datetime.date.today()}] ---\n")
    
    vulnerable_buckets_count = 0
    
    for bucket in aws_s3_buckets:
        bucket_name = bucket['Name']
        
        is_secure = audit_bucket(bucket)
        
        if is_secure:
            print(f"[✅ OK] Bucket '{bucket_name}' is encrypted.")
        else:
            print(f"[❌ ALERT] Bucket '{bucket_name}' is NOT ENCRYPTED!")
            vulnerable_buckets_count += 1
            
    print(f"\n--- SUMMARY: {vulnerable_buckets_count} vulnerable buckets found. ---")

if __name__ == "__main__":
    generate_report()
