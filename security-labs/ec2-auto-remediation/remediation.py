import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to detect and revoke insecure Security Group rules.
    Triggered by EventBridge on 'AuthorizeSecurityGroupIngress' API calls.
    """
    ec2 = boto3.client('ec2')

    detail = event.get('detail', {}) # Using .get() prevents crashes if keys are missing
    event_name = detail.get('eventName')
    
    request_params = detail.get('requestParameters', {})
    group_id = request_params.get('groupId')
    
    # Verify if it is an Ingress Rule creation event
    if event_name == 'AuthorizeSecurityGroupIngress':
        logger.info(f"Analyzing Security Group change for Group ID: {group_id}")
        
        ip_permissions = request_params.get('ipPermissions', {}).get('items', [])

        for rule in ip_permissions:
            ip_protocol = rule.get('ipProtocol')
            from_port = rule.get('fromPort')
            to_port = rule.get('toPort')
            ip_ranges = rule.get('ipRanges', {}).get('items', [])
            
            for ip_range in ip_ranges:
                cidr = ip_range.get('cidrIp')
                
                is_ssh_open = (from_port == 22 or to_port == 22) and cidr == '0.0.0.0/0'
                is_rdp_open = (from_port == 3389 or to_port == 3389) and cidr == '0.0.0.0/0'
                
                if is_ssh_open or is_rdp_open:
                    logger.warning(f"CRITICAL ALERT: Port {from_port} opened to the world (0.0.0.0/0) in {group_id}!")
                    
                    # REMEDIATION ACTION: Revoke the rule immediately
                    try:
                        logger.info(f"Attempting to revoke insecure rule in {group_id}...")
                        
                        ec2.revoke_security_group_ingress(
                            GroupId=group_id,
                            IpProtocol=ip_protocol,
                            FromPort=from_port,
                            ToPort=to_port,
                            CidrIp=cidr
                        )
                        logger.info("SUCCESS: Insecure rule revoked automatically. Compliance enforced.")
                        
                    except Exception as e:
                        logger.error(f"FAILED to remediate: {str(e)}")
                else:
                    logger.info(f"Safe rule detected: Port {from_port} allowed for {cidr}. No action taken.")

    return {
        'statusCode': 200,
        'body': json.dumps('Security Check Complete')
    }