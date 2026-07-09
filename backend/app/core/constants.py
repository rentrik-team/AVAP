"""Application-wide constants.

Values that remain fixed across all environments.
Configuration that varies by environment belongs in config.py.
"""

API_V1_PREFIX: str = "/api/v1"

DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200

TARGET_VALUE_MAX_LENGTH: int = 253
HOSTNAME_MAX_LABEL_LENGTH: int = 63
HOSTNAME_MAX_LENGTH: int = 253

CIDR_MIN_PREFIX_IPV4: int = 8
CIDR_MAX_PREFIX_IPV4: int = 32
