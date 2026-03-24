import boto3
import os

def lambda_handler(event, context):
    """
    Scans AWS IAM Users and sends an SNS alert if any user is missing MFA.
    Triggered daily via Amazon EventBridge.
    """
    iam = boto3.client('iam')
    sns = boto3.client('sns')
    topic_arn = os.environ['SNS_TOPIC_ARN']
    
    try:
        users = iam.list_users()['Users']
        users_without_mfa = []
        
        # Check MFA status for each user
        for user in users:
            mfa_devices = iam.list_mfa_devices(UserName=user['UserName'])
            if not mfa_devices['MFADevices']:
                users_without_mfa.append(user['UserName'])
        
        # If vulnerabilities found, send an alert
        if users_without_mfa:
            message = "CRITICAL SECURITY ALERT:\n\nThe following IAM Users do NOT have MFA enabled:\n"
            for u in users_without_mfa:
                message += f"- {u}\n"
            
            message += "\nPlease enforce MFA immediately to comply with CIS benchmarks."
            
            sns.publish(
                TopicArn=topic_arn,
                Subject="AWS IAM Security Alert: Missing MFA",
                Message=message
            )
            print(f"Alert sent for {len(users_without_mfa)} users.")
        else:
            print("All users are compliant. No alert needed.")
            
        return {"status": 200, "message": "Audit completed successfully."}
        
    except Exception as e:
        print(f"Error during audit: {str(e)}")
        raise e