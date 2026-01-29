import csv
import os
from contextvars import ContextVar
from datetime import datetime, timezone
from io import StringIO
import tzlocal
import time

from alibabacloud_bssopenapi20171214.client import Client as BssOpenApi20171214Client
from alibabacloud_credentials.provider import (
    StaticAKCredentialsProvider,
    StaticSTSCredentialsProvider,
    EcsRamRoleCredentialsProvider,
    RamRoleArnCredentialsProvider,
    OIDCRoleArnCredentialsProvider,
)
from alibabacloud_credentials.exceptions import CredentialException
from alibabacloud_credentials import provider
from alibabacloud_rds20140815.client import Client as RdsClient
from alibabacloud_tea_openapi.models import Config
from alibabacloud_vpc20160428.client import Client as VpcClient
from alibabacloud_das20200116.client import Client as DAS20200116Client


def _get_credentials_provider(self, config, profile_name):
    """
    Get credentials provider based on profile configuration.
    Supports multiple authentication modes: AK, StsToken, CloudSSO, RamRoleArn, EcsRamRole, OIDC, ChainableRamRoleArn.
    """
    if profile_name is None or profile_name == '':
        raise CredentialException('invalid profile name')

    profiles = config.get('profiles', [])

    if not profiles:
        raise CredentialException(f"unable to get profile with '{profile_name}' from cli credentials file.")

    for profile in profiles:
        if profile.get('name') is not None and profile['name'] == profile_name:
            mode = profile.get('mode')
            if mode == "AK":
                return StaticAKCredentialsProvider(
                    access_key_id=profile.get('access_key_id'),
                    access_key_secret=profile.get('access_key_secret')
                )
            elif mode == "StsToken" or mode == "CloudSSO":
                return StaticSTSCredentialsProvider(
                    access_key_id=profile.get('access_key_id'),
                    access_key_secret=profile.get('access_key_secret'),
                    security_token=profile.get('sts_token')
                )
            elif mode == "RamRoleArn":
                pre_provider = StaticAKCredentialsProvider(
                    access_key_id=profile.get('access_key_id'),
                    access_key_secret=profile.get('access_key_secret')
                )
                return RamRoleArnCredentialsProvider(
                    credentials_provider=pre_provider,
                    role_arn=profile.get('ram_role_arn'),
                    role_session_name=profile.get('ram_session_name'),
                    duration_seconds=profile.get('expired_seconds'),
                    policy=profile.get('policy'),
                    external_id=profile.get('external_id'),
                    sts_region_id=profile.get('sts_region'),
                    enable_vpc=profile.get('enable_vpc'),
                )
            elif mode == "EcsRamRole":
                return EcsRamRoleCredentialsProvider(
                    role_name=profile.get('ram_role_name')
                )
            elif mode == "OIDC":
                return OIDCRoleArnCredentialsProvider(
                    role_arn=profile.get('ram_role_arn'),
                    oidc_provider_arn=profile.get('oidc_provider_arn'),
                    oidc_token_file_path=profile.get('oidc_token_file'),
                    role_session_name=profile.get('role_session_name'),
                    duration_seconds=profile.get('expired_seconds'),
                    policy=profile.get('policy'),
                    sts_region_id=profile.get('sts_region'),
                    enable_vpc=profile.get('enable_vpc'),
                )
            elif mode == "ChainableRamRoleArn":
                previous_provider = self._get_credentials_provider(config, profile.get('source_profile'))
                return RamRoleArnCredentialsProvider(
                    credentials_provider=previous_provider,
                    role_arn=profile.get('ram_role_arn'),
                    role_session_name=profile.get('ram_session_name'),
                    duration_seconds=profile.get('expired_seconds'),
                    policy=profile.get('policy'),
                    external_id=profile.get('external_id'),
                    sts_region_id=profile.get('sts_region'),
                    enable_vpc=profile.get('enable_vpc'),
                )
            else:
                raise CredentialException(f"unsupported profile mode '{mode}' from cli credentials file.")

    raise CredentialException(f"unable to get profile with '{profile_name}' from cli credentials file.")


# Monkey patch CLIProfileCredentialsProvider to support CloudSSO and other modes
provider.cli_profile.CLIProfileCredentialsProvider._get_credentials_provider = _get_credentials_provider

current_request_headers: ContextVar[dict] = ContextVar("current_request_headers", default={})

PERF_KEYS = {
    "mysql": {
        "MemCpuUsage": ["MySQL_MemCpuUsage"],
        "QPSTPS": ["MySQL_QPSTPS"],
        "Sessions": ["MySQL_Sessions"],
        "COMDML": ["MySQL_COMDML"],
        "RowDML": ["MySQL_RowDML"],
        "SpaceUsage": ["MySQL_DetailedSpaceUsage"],
        "ThreadStatus": ["MySQL_ThreadStatus"],
        "MBPS": ["MySQL_MBPS"],
        "DetailedSpaceUsage": ["MySQL_DetailedSpaceUsage"]
    },
    "pgsql": {
        "MemCpuUsage": ["MemoryUsage", "CpuUsage"],
        "QPSTPS": ["PolarDBQPSTPS"],
        "Sessions": ["PgSQL_Session"],
        "COMDML": ["PgSQL_COMDML"],
        "RowDML": ["PolarDBRowDML"],
        "SpaceUsage": ["PgSQL_SpaceUsage"],
        "ThreadStatus": [],
        "MBPS": [],
        "DetailedSpaceUsage": ["SQLServer_DetailedSpaceUsage"]
    },
    "sqlserver": {
        "MemCpuUsage": ["SQLServer_CPUUsage"],
        "QPSTPS": ["SQLServer_QPS", "SQLServer_IOPS"],
        "Sessions": ["SQLServer_Sessions"],
        "COMDML": [],
        "RowDML": [],
        "SpaceUsage": ["SQLServer_DetailedSpaceUsage"],
        "ThreadStatus": [],
        "MBPS": [],
        "DetailedSpaceUsage": ["PgSQL_SpaceUsage"]
    }

}

DAS_KEYS = {
    "mysql": {
        "DiskUsage": ["disk_usage"],
        "IOPSUsage": ["data_iops_usage"],
        "IOBytesPS": ["data_io_bytes_ps"],
        "MdlLockSession": ["mdl_lock_session"]
    }
}


def parse_args(argv):
    args = {}
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('--'):
            key = arg[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith('--'):
                args[key] = argv[i+1]
                i += 2
            else:
                args[key] = True
                i += 1
    return args


def transform_to_iso_8601(dt: datetime, timespec: str):
    return dt.astimezone(timezone.utc).isoformat(timespec=timespec).replace("+00:00", "Z")

def parse_iso_8601(s: str) -> datetime:
    """
    将 ISO 8601 格式字符串（支持 Z 时区标记）转换为 datetime 对象。
    """
    # 替换 'Z' 为 '+00:00'，以便正确解析为 UTC 时间
    s = s.replace("Z", "+00:00")
    # 解析字符串为 UTC 时间的 datetime 对象
    dt_utc = datetime.fromisoformat(s)
    # 获取本地时区
    local_tz = tzlocal.get_localzone()
    # 转换为本地时区时间
    dt_local = dt_utc.astimezone(local_tz)
    return dt_local.replace(tzinfo=None)

def transform_timestamp_to_datetime(timestamp: int):
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def transform_to_datetime(s: str):
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M")
    return dt


def transform_perf_key(db_type: str, perf_keys: list[str]):
    perf_key_after_transform = []
    for key in perf_keys:
        if key in PERF_KEYS[db_type.lower()]:
            perf_key_after_transform.extend(PERF_KEYS[db_type.lower()][key])
        else:
            perf_key_after_transform.append(key)
    return perf_key_after_transform

def transform_das_key(db_type: str, das_keys: list[str]):
    das_key_after_transform = []
    for key in das_keys:
        if key in DAS_KEYS[db_type.lower()]:
            das_key_after_transform.extend(DAS_KEYS[db_type.lower()][key])
        else:
            das_key_after_transform.append(key)
    return das_key_after_transform


def json_array_to_csv(data):
    if not data or not isinstance(data, list):
        return ""

    fieldnames = set()
    for item in data:
        if isinstance(item, dict):
            fieldnames.update(item.keys())
        elif hasattr(item, 'to_map'):
            fieldnames.update(item.to_map().keys())

    if not fieldnames:
        return ""

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=sorted(fieldnames))

    writer.writeheader()
    for item in data:
        if isinstance(item, dict):
            writer.writerow({k: v if v is not None else '' for k, v in item.items()})
        elif hasattr(item, 'to_map'):
            writer.writerow({k: v if v is not None else '' for k, v in item.to_map().items()})

    return output.getvalue()


def json_array_to_markdown(headers, datas):
    if not headers or not isinstance(headers, list):
        return ""
    if not datas or not isinstance(datas, list):
        return ""
    
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in datas:
        if isinstance(row, dict):
            markdown_table += "| " + " | ".join(str(row.get(header, '-')) for header in headers) + " |\n"
        else:
            markdown_table += "| " + " | ".join(map(str, row)) + " |\n"
    return markdown_table

def convert_datetime_to_timestamp(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    timestamp_seconds = time.mktime(dt.timetuple())
    timestamp_milliseconds = int(timestamp_seconds) * 1000
    return timestamp_milliseconds


def get_rds_account():
    header = current_request_headers.get()
    user = header.get("rds_user") if header else None
    passwd = header.get("rds_passwd") if header else None
    if user and passwd:
        return user, passwd
    return None, None


def get_aksk():
    """
    Get credentials from environment variables or request headers.
    Supports both static AK/SK and STS Token.
    """
    ak = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    sk = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    sts = os.getenv('ALIBABA_CLOUD_SECURITY_TOKEN')
    header = current_request_headers.get()
    if header and (header.get("ak") or header.get("sk") or header.get("sts")):
        ak, sk, sts = header.get("ak"), header.get("sk"), header.get("sts")
    return ak, sk, sts


def get_credentials():
    """
    Get credentials using the default credential chain.
    This supports multiple authentication modes including:
    - Static AK/SK from environment variables
    - STS Token from environment variables
    - CloudSSO from aliyun CLI config
    - ECS RAM Role
    - OIDC
    - RAM Role ARN

    Returns:
        tuple: (access_key_id, access_key_secret, security_token)
    """
    from alibabacloud_credentials.client import Client as CredentialClient
    from alibabacloud_credentials.models import Config as CredentialConfig

    header = current_request_headers.get()
    if header and (header.get("ak") or header.get("sk") or header.get("sts")):
        return header.get("ak"), header.get("sk"), header.get("sts")

    ak = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
    sk = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
    if ak and sk:
        sts = os.getenv('ALIBABA_CLOUD_SECURITY_TOKEN')
        return ak, sk, sts

    try:
        profile_name = os.getenv('ALIBABA_CLOUD_PROFILE')
        if profile_name:
            from alibabacloud_credentials.provider import CLIProfileCredentialsProvider
            cred_provider = CLIProfileCredentialsProvider(profile_name=profile_name)
            credential = cred_provider.get_credentials()
            return (
                credential.get_access_key_id(),
                credential.get_access_key_secret(),
                credential.get_security_token()
            )
        else:
            cred_config = CredentialConfig()
            cred_client = CredentialClient(cred_config)
            credential = cred_client.get_credential()
            return (
                credential.access_key_id,
                credential.access_key_secret,
                credential.security_token
            )
    except Exception:
        return None, None, None


def get_rds_client(region_id: str):
    ak, sk, sts = get_credentials()
    config = Config(
        access_key_id=ak,
        access_key_secret=sk,
        security_token=sts,
        region_id=region_id,
        protocol="https",
        connect_timeout=10 * 1000,
        read_timeout=300 * 1000
    )
    client = RdsClient(config)
    return client


def get_vpc_client(region_id: str) -> VpcClient:
    """Get VPC client instance.

    Args:
        region_id: The region ID for the VPC client.

    Returns:
        VpcClient: The VPC client instance for the specified region.
    """
    ak, sk, sts = get_credentials()
    config = Config(
        access_key_id=ak,
        access_key_secret=sk,
        security_token=sts,
        region_id=region_id,
        protocol="https",
        connect_timeout=10 * 1000,
        read_timeout=300 * 1000
    )
    return VpcClient(config)


def get_bill_client(region_id: str):
    ak, sk, sts = get_credentials()
    config = Config(
        access_key_id=ak,
        access_key_secret=sk,
        security_token=sts,
        region_id=region_id,
        protocol="https",
        connect_timeout=10 * 1000,
        read_timeout=300 * 1000
    )
    client = BssOpenApi20171214Client(config)
    return client


def get_das_client():
    ak, sk, sts = get_credentials()
    config = Config(
        access_key_id=ak,
        access_key_secret=sk,
        security_token=sts,
        region_id='cn-shanghai',
        protocol="https",
        connect_timeout=10 * 1000,
        read_timeout=300 * 1000
    )
    client = DAS20200116Client(config)
    return client
