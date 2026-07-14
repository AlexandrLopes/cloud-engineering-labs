import boto3
import datetime
from botocore.exceptions import ClientError

INACTIVITY_THRESHOLD_DAYS = 90


def get_days_since(reference_date):
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - reference_date
    return diff.days


def audit_iam_users():
    iam = boto3.client('iam')

    print(f"{'USER':<20} | {'MFA':<10} | {'LOGIN INACTIVITY':<20} | {'KEY AGE (Days)':<15} | {'STATUS'}")
    print("-" * 95)

    try:
        users = iam.list_users()['Users']

        for user in users:
            username = user['UserName']

            # 1. Verify MFA
            mfa_list = iam.list_mfa_devices(UserName=username)['MFADevices']
            has_mfa = "Enabled" if mfa_list else "DISABLED "

            # 2. Login inactivity — the check the README always promised but the
            #    code never actually implemented. PasswordLastUsed is only set
            #    for users with console access; it's absent for API-only users.
            password_last_used = user.get('PasswordLastUsed')
            if password_last_used is None:
                # Could mean "never logged in via console" OR "no console access
                # at all (API/CLI only user)" — both read the same from this API,
                # so the label is deliberately neutral rather than alarmist.
                login_status = "No console login"
                login_flag = "N/A (no console access)"
            else:
                inactivity_days = get_days_since(password_last_used)
                login_status = f"{inactivity_days} days ago"
                if inactivity_days > INACTIVITY_THRESHOLD_DAYS:
                    login_flag = f"STALE: {inactivity_days}d inactive"
                else:
                    login_flag = "Active"

            # 3. Verify Access Keys
            keys = iam.list_access_keys(UserName=username)['AccessKeyMetadata']

            if not keys:
                print(f"{username:<20} | {has_mfa:<10} | {login_status:<20} | {'None':<15} | {login_flag}")
                continue

            for key in keys:
                status = key['Status']
                create_date = key['CreateDate']
                age_days = get_days_since(create_date)

                # (CIS Benchmark) — key rotation check, unchanged from the
                # original tool, now reported alongside login inactivity
                # instead of as the only signal.
                if status == "Active" and age_days > 90:
                    key_alert = "CRITICAL: ROTATE KEY!"
                elif status == "Active" and age_days > 60:
                    key_alert = "WARNING: Plan rotation"
                else:
                    key_alert = "OK"

                # Combine both signals into one status column — a user can be
                # flagged for either stale login, an old key, or both.
                combined_status = key_alert if key_alert != "OK" else login_flag

                print(f"{username:<20} | {has_mfa:<10} | {login_status:<20} | {str(age_days) + ' days':<15} | {combined_status}")

    except ClientError as e:
        print(f"Erro ao conectar na AWS: {e}")


if __name__ == "__main__":
    audit_iam_users()
