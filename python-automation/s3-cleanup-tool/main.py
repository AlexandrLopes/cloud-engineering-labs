import boto3
from datetime import datetime, timezone

# CONFIGURATION
BUCKET_NAME = 'nome-do-seu-bucket-de-teste' # Troque pelo seu bucket real quando for testar
DAYS_TO_KEEP = 30 

def clean_old_files():
    """
    Deletes files from an S3 bucket that are older than DAYS_TO_KEEP.
    """
    s3 = boto3.client('s3')
    
    try:
        # List objects in the bucket
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            print(f"Bucket {BUCKET_NAME} is empty.")
            return

        today = datetime.now(timezone.utc)
        deleted_count = 0

        print(f" Checking for files older than {DAYS_TO_KEEP} days...")

        for obj in response['Contents']:
            file_date = obj['LastModified']
            file_name = obj['Key']
            
            # Calculate file age
            age_days = (today - file_date).days
            
            if age_days > DAYS_TO_KEEP:
                print(f" Deleting: {file_name} ({age_days} days old)")
                # DELETE COMMAND - Uncomment below to actually delete
                # s3.delete_object(Bucket=BUCKET_NAME, Key=file_name)
                deleted_count += 1
            else:
                print(f" Kept: {file_name} ({age_days} days old)")

        print(f"\nSummary: {deleted_count} files processed for deletion.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_old_files()
