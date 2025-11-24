import boto3
from datetime import datetime, timezone
import sys

# --- CONFIGURATION ---
# Define the threshold for inactivity (industry standard is often 90 days)
INACTIVITY_THRESHOLD_DAYS = 90

def audit_iam_users():
    """
    Audits AWS IAM users to identify inactive accounts that pose a security risk.
    """
    # Create IAM client
    iam = boto3.client('iam')
    
    print("🛡️  Starting IAM Security Audit...\n")
    print(f"Criteria: Users inactive for more than {INACTIVITY_THRESHOLD_DAYS} days.\n")
    print(f"{'USER':<25} | {'STATUS':<15} | {'LAST LOGIN':<20} | {'DAYS INACTIVE'}")
    print("-" * 80)

    try:
        # Get list of all users
        # Note: For production with >1000 users, you would need to implement pagination.
        response = iam.list_users()
        
        issues_found = 0
        
        for user in response['Users']:
            username = user['UserName']
            
            # Check if the user has a password and when it was last used
            if 'PasswordLastUsed' in user:
                last_used = user['PasswordLastUsed']
                
                # Calculate days since last login
                now = datetime.now(timezone.utc)
                days_inactive = (now - last_used).days
                
                if days_inactive > INACTIVITY_THRESHOLD_DAYS:
                    status = "⚠️ WARNING"
                    issues_found += 1
                    print(f"{username:<25} | {status:<15} | {last_used.strftime('%Y-%m-%d')}       | {days_inactive} days")
                else:
                    status = "✅ ACTIVE"
                    # Optional: Uncomment to see active users too
                    # print(f"{username:<25} | {status:<15} | {last_used.strftime('%Y-%m-%d')}       | {days_inactive} days")
            
            else:
                # User exists but never used the password (or only uses Access Keys)
                # This is also a potential risk if it's an old account
                creation_date = user['CreateDate']
                now = datetime.now(timezone.utc)
                days_since_creation = (now - creation_date).days

                if days_since_creation > INACTIVITY_THRESHOLD_DAYS:
                    print(f"{username:<25} |  NEVER LOGGED  | N/A                  | {days_since_creation} days (Created)")
                    issues_found += 1

        print("-" * 80)
        print(f"\n Audit Complete. Found {issues_found} users requiring attention.")
        
        if issues_found > 0:
            print("Recommendation: Review these accounts and disable/delete if not needed.")

    except Exception as e:
        print(f"Error connecting to AWS: {e}")
        print("Tip: Check if your credentials are configured correctly (aws configure).")

if __name__ == "__main__":
    audit_iam_users()
