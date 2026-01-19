import boto3
import datetime
from botocore.exceptions import ClientError

def get_days_since_creation(create_date):
    #  timezone UTC 
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - create_date
    return diff.days

def audit_iam_users():
    iam = boto3.client('iam')
    
    print(f"{'USER':<20} | {'MFA':<10} | {'KEY AGE (Days)':<15} | {'STATUS'}")
    print("-" * 65)

    try:
        users = iam.list_users()['Users']
        
        for user in users:
            username = user['UserName']
            
            # 1. Verify MFA
            mfa_list = iam.list_mfa_devices(UserName=username)['MFADevices']
            has_mfa = "Enabled" if mfa_list else "DISABLED "
            
            # 2. Verify Access Keys
            keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']
            
            if not keys:
                print(f"{username:<20} | {has_mfa:<10} | {'None':<15} | {'OK'}")
            
            for key in keys:
                key_id = key['AccessKeyId']
                status = key['Status'] # Active ou Inactive
                create_date = key['CreateDate']
                
                # age of the keys
                age_days = get_days_since_creation(create_date)
                
                # (CIS Benchmark)
                security_alert = ""
                if status == "Active" and age_days > 90:
                    security_alert = "CRITICAL: ROTATE KEY! "
                elif status == "Active" and age_days > 60:
                    security_alert = "WARNING: Plan rotation "
                else:
                    security_alert = "OK "

                print(f"{username:<20} | {has_mfa:<10} | {str(age_days) + ' days':<15} | {security_alert}")

    except ClientError as e:
        print(f"Erro ao conectar na AWS: {e}")

if __name__ == "__main__":
    audit_iam_users()