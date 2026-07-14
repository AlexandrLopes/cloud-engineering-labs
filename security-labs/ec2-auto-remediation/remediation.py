import boto3
import json
import logging
import os
import time
import uuid
import ipaddress
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RISKY_PORTS = (22, 3389)

# Comma-separated list of known-legitimate CIDR ranges (e.g. corporate VPN)
# exempt from remediation. Empty by default.
ALLOWED_CIDRS = [
    c.strip() for c in os.environ.get('ALLOWED_CIDR_RANGES', '').split(',') if c.strip()
]

ALERTS_TABLE_NAME = "SecurityAlerts"
ALERTS_REGION = "us-east-1"


def log_alert(severity, message):
    """Writes a finding to the shared SecurityAlerts table (see
    dynamodb-security-log in this portfolio). Best-effort — a missing table
    or write failure is logged but never blocks remediation itself."""
    try:
        table = boto3.resource('dynamodb', region_name=ALERTS_REGION).Table(ALERTS_TABLE_NAME)
        table.put_item(Item={
            'alert_id': str(uuid.uuid4()),
            'timestamp': str(time.time()),
            'severity': severity,
            'message': message,
            'status': 'RESOLVED' if severity != "INFO" else 'OPEN',
            'source': 'ec2-auto-remediation',
        })
    except ClientError as e:
        logger.warning(f"Could not write to SecurityAlerts table: {e.response['Error']['Code']}")


def _is_allowlisted(cidr, allowed_cidrs):
    """True if `cidr` is contained within (or equal to) any allowed range."""
    try:
        target = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False

    for allowed in allowed_cidrs:
        try:
            allowed_net = ipaddress.ip_network(allowed, strict=False)
            if target.version == allowed_net.version and target.subnet_of(allowed_net):
                return True
        except ValueError:
            logger.warning(f"Skipping malformed entry in ALLOWED_CIDR_RANGES: {allowed}")
    return False


def _port_is_risky(from_port, to_port):
    if from_port is None or to_port is None:
        # No FromPort/ToPort means "all ports" (IpProtocol == "-1").
        return True
    return any(from_port <= p <= to_port for p in RISKY_PORTS)


def lambda_handler(event, context):
    """
    Detects and revokes insecure Security Group rules.
    Triggered by EventBridge on 'AuthorizeSecurityGroupIngress' API calls.
    """
    ec2 = boto3.client('ec2')

    detail = event.get('detail', {})
    event_name = detail.get('eventName')

    request_params = detail.get('requestParameters', {})
    group_id = request_params.get('groupId')

    if event_name != 'AuthorizeSecurityGroupIngress':
        return {'statusCode': 200, 'body': json.dumps('Not a relevant event, no action taken.')}

    logger.info(f"Analyzing Security Group change for Group ID: {group_id}")

    ip_permissions = request_params.get('ipPermissions', {}).get('items', [])

    for rule in ip_permissions:
        rule_protocol = rule.get('ipProtocol')
        from_port = rule.get('fromPort')
        to_port = rule.get('toPort')
        is_all_traffic = rule_protocol == '-1'

        ip_ranges = rule.get('ipRanges', {}).get('items', [])
        for ip_range in ip_ranges:
            cidr = ip_range.get('cidrIp')
            _evaluate_and_remediate(ec2, group_id, rule_protocol, from_port, to_port, cidr, is_all_traffic)

        ipv6_ranges = rule.get('ipv6Ranges', {}).get('items', [])
        for ip_range in ipv6_ranges:
            cidr = ip_range.get('cidrIpv6')
            _evaluate_and_remediate(ec2, group_id, rule_protocol, from_port, to_port, cidr, is_all_traffic)

    return {
        'statusCode': 200,
        'body': json.dumps('Security Check Complete')
    }


def _evaluate_and_remediate(ec2, group_id, ip_protocol, from_port, to_port, cidr, is_all_traffic):
    if cidr is None:
        return

    is_public = cidr in ('0.0.0.0/0', '::/0')
    if not is_public:
        logger.info(f"Safe rule detected: {cidr} is not a public range. No action taken.")
        return

    if not _port_is_risky(from_port, to_port):
        logger.info(f"Safe rule detected: port {from_port} on {cidr} is not in the risky-port list. No action taken.")
        return

    if _is_allowlisted(cidr, ALLOWED_CIDRS):
        logger.info(f"Rule on {cidr} matches an allowlisted range — legitimate access, no action taken.")
        return

    label = "ALL PORTS (all-traffic rule)" if is_all_traffic else f"port {from_port}"
    logger.warning(f"CRITICAL ALERT: {label} opened to {cidr} in {group_id}!")

    try:
        logger.info(f"Attempting to revoke insecure rule in {group_id}...")
        revoke_kwargs = {
            'GroupId': group_id,
            'IpProtocol': ip_protocol,
        }
        if not is_all_traffic:
            revoke_kwargs['FromPort'] = from_port
            revoke_kwargs['ToPort'] = to_port
        if ':' in cidr:
            revoke_kwargs['CidrIpv6'] = cidr
        else:
            revoke_kwargs['CidrIp'] = cidr

        ec2.revoke_security_group_ingress(**revoke_kwargs)
        logger.info("SUCCESS: Insecure rule revoked automatically. Compliance enforced.")
        log_alert("CRITICAL", f"Auto-revoked {label} opened to {cidr} on {group_id}")

    except Exception as e:
        logger.error(f"FAILED to remediate: {str(e)}")
        log_alert("CRITICAL", f"FAILED to revoke {label} opened to {cidr} on {group_id}: {str(e)}")
