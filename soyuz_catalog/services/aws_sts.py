"""AWS STS assume-role helper for credential vending.

Isolated from :mod:`soyuz_catalog.services.credentials_service` so the
``boto3`` import — the only AWS SDK dependency in the project — stays in
one place and is loaded lazily, only when STS vending is actually
enabled and a role is being assumed. Everything else in soyuz stays
boto3-free.
"""

from __future__ import annotations

from soyuz_catalog.api.schemas import AwsCredentials


def assume_role_credentials(
    *,
    role_arn: str,
    external_id: str | None,
    region: str,
    duration_seconds: int,
    session_name: str,
) -> AwsCredentials:
    """Assume an IAM role via STS and return the short-lived keys.

    Args:
        role_arn: The IAM role ARN to assume.
        external_id: The role's ``ExternalId`` confused-deputy guard, or
            ``None`` when the role does not require one.
        region: AWS region for the STS client; empty string lets boto3
            resolve the region itself.
        duration_seconds: Requested session lifetime; AWS clamps it to
            the role's ``MaxSessionDuration``.
        session_name: A label for the assumed-role session (shows up in
            CloudTrail), derived from the requested operation.

    Returns:
        AwsCredentials: The vended access-key / secret / session-token
            triple from the STS response.
    """
    import boto3

    client = boto3.client("sts", region_name=region or None)
    params: dict[str, object] = {
        "RoleArn": role_arn,
        "RoleSessionName": session_name,
        "DurationSeconds": duration_seconds,
    }
    if external_id:
        params["ExternalId"] = external_id
    response = client.assume_role(**params)  # type: ignore[arg-type]
    creds = response["Credentials"]
    return AwsCredentials(
        access_key_id=creds["AccessKeyId"],
        secret_access_key=creds["SecretAccessKey"],
        session_token=creds["SessionToken"],
    )
