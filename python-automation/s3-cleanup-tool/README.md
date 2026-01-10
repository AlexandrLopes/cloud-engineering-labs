# AWS S3 Automated Cleanup Tool

This project is a Python script designed to automate **Cloud Cost Optimization**. It scans a specific AWS S3 Bucket and identifies/deletes objects older than a defined period (e.g., 30 days).

### Why this project?
In Cloud Engineering, storing logs, backups, or temporary files indefinitely can lead to unnecessary costs. This script solves that problem by automating the lifecycle of objects using logic that can be customized beyond standard AWS Lifecycle Rules.

### Technologies
* **Language:** Python 3
* **SDK:** AWS Boto3
* **Service:** Amazon S3

### How it works
1.  The script connects to AWS using the `boto3` client.
2.  It lists all objects in the target bucket.
3.  It compares the `LastModified` date of each file with the current date.
4.  If the file is older than `DAYS_TO_KEEP`, it is flagged for deletion.

### ⚠️ Safety First (Dry Run)
By default, the delete command in `main.py` is commented out to prevent accidental data loss during testing. This is a "Dry Run" mode to visualize what *would* happen.

### How to run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your AWS Credentials
aws configure

# 3. Run the script
python main.py
