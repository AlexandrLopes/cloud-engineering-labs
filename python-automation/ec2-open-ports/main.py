import time
import uuid

import boto3
from botocore.exceptions import ClientError

# CONFIGURATION
RISKY_PORTS = [22, 3389, 8080]
IPV4_OPEN = '0.0.0.0/0'
IPV6_OPEN = '::/0'

ALERTS_TABLE_NAME = "SecurityAlerts"
ALERTS_REGION = "us-east-1"


def log_alert(severity, message):
    """Writes a finding to the shared SecurityAlerts table (see
    dynamodb-security-log in this portfolio). The table is provisioned by
    that project, not created here — if it doesn't exist yet, this logs a
    warning and the audit continues normally. Console output is the primary
    result of this script; DynamoDB logging is a secondary, best-effort step."""
    try:
        table = boto3.resource('dynamodb', region_name=ALERTS_REGION).Table(ALERTS_TABLE_NAME)
        table.put_item(Item={
            'alert_id': str(uuid.uuid4()),
            'timestamp': str(time.time()),
            'severity': severity,
            'message': message,
            'status': 'OPEN',
            'source': 'ec2-open-ports',
        })
    except ClientError as e:
        print(f"  (Could not write to SecurityAlerts table: {e.response['Error']['Code']})")


def _port_is_risky(from_port, to_port):
    if from_port is None or to_port is None:
        # No FromPort/ToPort means "all ports" (IpProtocol == "-1") —
        # the widest possible exposure, always risky regardless of RISKY_PORTS.
        return True
    return any(from_port <= p <= to_port for p in RISKY_PORTS)


def audit_security_groups():
    # Audits AWS Security Groups to find public open ports (IPv4 and IPv6),
    # including "all traffic" rules that have no FromPort/ToPort at all.
    ec2 = boto3.client('ec2')

    try:
        print(" Scanning Security Groups for risky configurations...")
        response = ec2.describe_security_groups()

        risky_count = 0

        for sg in response['SecurityGroups']:
            sg_name = sg['GroupName']
            sg_id = sg['GroupId']

            for rule in sg['IpPermissions']:  # Check inbound rules (Ingress)
                from_port = rule.get('FromPort')
                to_port = rule.get('ToPort', from_port)
                is_all_traffic = rule.get('IpProtocol') == '-1'

                # IPv4 exposure
                for ip_range in rule.get('IpRanges', []):
                    cidr = ip_range.get('CidrIp')
                    if cidr == IPV4_OPEN and _port_is_risky(from_port, to_port):
                        risky_count += 1
                        if is_all_traffic:
                            print(f"  CRITICAL! ALL TRAFFIC open to the internet (IPv4)!")
                            print(f"    - Group: {sg_name} ({sg_id})")
                            print(f"    - Protocol: ALL PORTS OPEN to 0.0.0.0/0")
                            log_alert("CRITICAL", f"All-traffic rule open to 0.0.0.0/0 on {sg_id} ({sg_name})")
                        else:
                            print(f"  ALERT! Risky Open Port found!")
                            print(f"    - Group: {sg_name} ({sg_id})")
                            print(f"    - Port: {from_port} OPEN to Internet (0.0.0.0/0)")
                            log_alert("HIGH", f"Port {from_port} open to 0.0.0.0/0 on {sg_id} ({sg_name})")

                # IPv6 exposure — the check that didn't exist before.
                for ip_range in rule.get('Ipv6Ranges', []):
                    cidr = ip_range.get('CidrIpv6')
                    if cidr == IPV6_OPEN and _port_is_risky(from_port, to_port):
                        risky_count += 1
                        if is_all_traffic:
                            print(f"  CRITICAL! ALL TRAFFIC open to the internet (IPv6)!")
                            print(f"    - Group: {sg_name} ({sg_id})")
                            print(f"    - Protocol: ALL PORTS OPEN to ::/0")
                            log_alert("CRITICAL", f"All-traffic rule open to ::/0 on {sg_id} ({sg_name})")
                        else:
                            print(f"  ALERT! Risky Open Port found (IPv6)!")
                            print(f"    - Group: {sg_name} ({sg_id})")
                            print(f"    - Port: {from_port} OPEN to Internet (::/0)")
                            log_alert("HIGH", f"Port {from_port} open to ::/0 on {sg_id} ({sg_name})")

        if risky_count == 0:
            print("\n Audit Complete: No risky open ports found.")
        else:
            print(f"\n Audit Complete: Found {risky_count} security risks.")

    except Exception as e:
        print(f"Error checking Security Groups: {e}")


if __name__ == "__main__":
    audit_security_groups()
