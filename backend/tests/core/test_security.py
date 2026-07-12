import pytest

from app.core.security import is_valid_hostname, is_valid_ipv4, is_valid_ipv4_cidr

# --- Regression: dotted-quad-shaped strings must never classify as hostnames ---


@pytest.mark.parametrize(
    "invalid_dotted_value",
    [
        "999.999.999.999",  # out-of-range octets
        "300.400.500.600",  # out-of-range octets
        "1.2.3.4.5",  # too many numeric labels
        "1.2.3",  # too few numeric labels
    ],
)
def test_is_valid_hostname_rejects_numeric_dotted_values(invalid_dotted_value):
    """A value composed entirely of numeric, dot-separated labels is always
    an attempted IP address and must never be accepted as a hostname, even
    when ipaddress.IPv4Address() fails to parse it (e.g. invalid octets or
    wrong octet count). Regression for a defect where such values fell
    through to hostname classification after the IPv4 parse raised.
    """
    assert is_valid_hostname(invalid_dotted_value) is False
    assert is_valid_ipv4(invalid_dotted_value) is False
    assert is_valid_ipv4_cidr(invalid_dotted_value) is False


def test_is_valid_hostname_rejects_valid_looking_ip():
    """A syntactically valid IPv4 address must not also be accepted as a hostname."""
    assert is_valid_hostname("192.168.1.1") is False
    assert is_valid_ipv4("192.168.1.1") is True


@pytest.mark.parametrize(
    "valid_hostname",
    [
        "example.com",
        "www.google.com",
        "internal-server",
        "host.internal.corp",
        "3.example.com",  # a single numeric label alongside non-numeric labels is fine
    ],
)
def test_is_valid_hostname_accepts_valid_hostnames(valid_hostname):
    assert is_valid_hostname(valid_hostname) is True


# --- is_valid_ipv4 / is_valid_ipv4_cidr basic contract ---


@pytest.mark.parametrize(
    "ip",
    ["192.168.1.1", "8.8.8.8", "203.0.113.5"],
)
def test_is_valid_ipv4_accepts_valid_addresses(ip):
    assert is_valid_ipv4(ip) is True


@pytest.mark.parametrize(
    "cidr",
    ["10.0.0.0/8", "192.168.1.0/24"],
)
def test_is_valid_ipv4_cidr_accepts_valid_networks(cidr):
    assert is_valid_ipv4_cidr(cidr) is True
