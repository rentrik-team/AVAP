import ipaddress
import re

from app.core.constants import HOSTNAME_MAX_LABEL_LENGTH, HOSTNAME_MAX_LENGTH

# Regex for validating a single hostname label
# Must start and end with alphanumeric, can contain hyphens
_LABEL_REGEX = re.compile(
    rf"^[a-zA-Z0-9]([a-zA-Z0-9-]{{0,{HOSTNAME_MAX_LABEL_LENGTH - 2}}}[a-zA-Z0-9])?$"
)


def is_valid_ipv4(ip_str: str) -> bool:
    """Validate if a string is a valid IPv4 address.
    
    Args:
        ip_str: The string to validate.
        
    Returns:
        True if valid IPv4 address, False otherwise.
    """
    try:
        ip = ipaddress.IPv4Address(ip_str)
        return not (ip.is_multicast or ip.is_loopback or ip.is_unspecified)
    except ipaddress.AddressValueError:
        return False


def is_valid_ipv4_cidr(cidr_str: str) -> bool:
    """Validate if a string is a valid IPv4 CIDR network.
    
    Args:
        cidr_str: The string to validate.
        
    Returns:
        True if valid IPv4 network, False otherwise.
    """
    try:
        network = ipaddress.IPv4Network(cidr_str, strict=False)
        return not (
            network.is_multicast or network.is_loopback or network.is_unspecified
        )
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
        return False


def is_valid_hostname(hostname: str) -> bool:
    """Validate if a string is an RFC-compliant hostname.
    
    Args:
        hostname: The string to validate.
        
    Returns:
        True if valid hostname, False otherwise.
    """
    if not hostname or len(hostname) > HOSTNAME_MAX_LENGTH:
        return False

    # Remove trailing dot if present (FQDN)
    if hostname.endswith("."):
        hostname = hostname[:-1]

    labels = hostname.split(".")
    
    # Needs at least one label, though usually we expect a TLD (2+)
    # For flexibility in internal networks, we allow single labels
    if not labels:
        return False

    for label in labels:
        if not _LABEL_REGEX.match(label):
            return False

    # A valid hostname shouldn't look like an IP address
    # We do a quick check here, though is_valid_ipv4 is more robust
    try:
        ipaddress.IPv4Address(hostname)
        return False # It's an IP, not a hostname
    except ipaddress.AddressValueError:
        pass

    return True


def normalize_target_value(value: str) -> str:
    """Normalize a target value for consistent storage and comparison.
    
    - Strips leading/trailing whitespace
    - Converts to lowercase
    
    Args:
        value: The raw target string.
        
    Returns:
        The normalized target string.
    """
    return value.strip().lower()
