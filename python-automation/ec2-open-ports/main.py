import boto3
import json

# CONFIGURATION

RISKY_PORTS = [22, 3389, 8080] 

def audit_security_groups():
    
    #Audits AWS Security Groups to find public open ports.
    ec2 = boto3.client('ec2')
    
    try:
        # Get all Security Groups
        print(" Scanning Security Groups for risky configurations...")
        response = ec2.describe_security_groups()
        
        risky_count = 0

        for sg in response['SecurityGroups']:
            sg_name = sg['GroupName']
            sg_id = sg['GroupId']
            
            for rule in sg['IpPermissions']: # Check inbound rules (Ingress)
                if 'FromPort' in rule:
                    from_port = rule['FromPort']
                    to_port = rule.get('ToPort', from_port)
                    
                    for ip_range in rule['IpRanges']: # Check if connection is open to the world (0.0.0.0/0)
                        cidr = ip_range.get('CidrIp')
                        
                        if cidr == '0.0.0.0/0':
                            if from_port in RISKY_PORTS or to_port in RISKY_PORTS:
                                print(f"⚠️  ALERT! Risky Open Port found!")
                                print(f"    - Group: {sg_name} ({sg_id})")
                                print(f"    - Port: {from_port} OPEN to Internet (0.0.0.0/0)")
                                risky_count += 1

        if risky_count == 0:
            print("\n Audit Complete: No risky open ports found.")
        else:
            print(f"\n Audit Complete: Found {risky_count} security risks.")

    except Exception as e:
        print(f"Error checking Security Groups: {e}")

if __name__ == "__main__":
    audit_security_groups()
