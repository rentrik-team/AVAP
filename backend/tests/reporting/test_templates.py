from app.core.enums import RiskLevel
from app.reporting import templates


def test_safe_text_escapes_font_tag():
    result = templates.safe_text("<font color=red>Injected</font>")
    assert "<font" not in result
    assert "&lt;font" in result


def test_safe_text_escapes_img_tag():
    result = templates.safe_text('<img src="x" onerror="alert(1)">')
    assert "<img" not in result
    assert "&lt;img" in result


def test_safe_text_escapes_anchor_tag():
    result = templates.safe_text('<a href="http://evil.example">click</a>')
    assert "<a href" not in result
    assert "&lt;a" in result


def test_safe_text_escapes_ampersand_and_angle_brackets():
    result = templates.safe_text("A & B < C > D")
    assert result == "A &amp; B &lt; C &gt; D"


def test_safe_text_handles_none_and_empty():
    assert templates.safe_text(None) == ""
    assert templates.safe_text("") == ""


def test_safe_text_handles_malformed_xml_like_content():
    malformed = "<unclosed <<< >>> tag"
    result = templates.safe_text(malformed)
    assert "<unclosed" not in result


def test_safe_text_handles_very_long_strings():
    long_value = "A" * 50000
    result = templates.safe_text(long_value)
    assert len(result) == 50000


def test_risk_level_color_returns_distinct_colors_per_level():
    colors_seen = {templates.risk_level_color(level) for level in RiskLevel}
    assert len(colors_seen) == len(list(RiskLevel))


def test_get_styles_returns_expected_style_keys():
    styles = templates.get_styles()
    for key in ("Title", "Heading1", "Heading2", "Body", "Meta", "Small"):
        assert key in styles


def test_heading_and_body_text_escape_content():
    styles = templates.get_styles()
    heading = templates.heading("<script>alert(1)</script>", 1, styles)
    body = templates.body_text("<b>bold</b> attempt", styles)
    assert "&lt;script&gt;" in heading.text
    assert "&lt;b&gt;" in body.text
