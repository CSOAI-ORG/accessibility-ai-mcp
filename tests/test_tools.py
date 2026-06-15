"""Functional tests for Accessibility AI MCP Server tools.

Tests color contrast, alt text suggestions, heading hierarchy,
and ARIA validation. No external API calls.
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch

_mock_mcp_module = MagicMock()

class _MockFastMCP:
    def __init__(self, name="", **kwargs):
        self.name = name

    def tool(self):
        def decorator(fn):
            return fn
        return decorator

_mock_mcp_module.FastMCP = _MockFastMCP
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = _mock_mcp_module

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.pop("MEOK_API_KEY", None)

import server as srv  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state():
    srv._call_counts.clear()
    yield
    srv._call_counts.clear()


@pytest.fixture(autouse=True)
def bypass_auth_and_rate_limit():
    with patch.object(srv, "check_access", return_value=(True, "OK", "pro")), \
         patch.object(srv, "_check_rate_limit", return_value=None):
        yield


class TestMcpRegistration:
    def test_mcp_object_exists(self):
        assert hasattr(srv, "mcp")

    def test_all_tools_callable(self):
        tool_names = [
            "check_color_contrast", "suggest_alt_text",
            "check_heading_hierarchy", "aria_validator",
        ]
        for name in tool_names:
            assert callable(getattr(srv, name)), f"Tool not callable: {name}"


class TestHelperFunctions:
    def test_hex_to_rgb_short(self):
        assert srv._hex_to_rgb("#FFF") == (255, 255, 255)

    def test_hex_to_rgb_full(self):
        assert srv._hex_to_rgb("#333333") == (51, 51, 51)

    def test_hex_to_rgb_black(self):
        assert srv._hex_to_rgb("#000000") == (0, 0, 0)

    def test_hex_to_rgb_red(self):
        assert srv._hex_to_rgb("#FF0000") == (255, 0, 0)

    def test_relative_luminance_black(self):
        assert srv._relative_luminance(0, 0, 0) == 0.0

    def test_relative_luminance_white(self):
        assert round(srv._relative_luminance(255, 255, 255), 4) == 1.0


class TestCheckColorContrast:
    def test_black_on_white_aa(self):
        result = srv.check_color_contrast("#000000", "#FFFFFF")
        assert result["contrast_ratio"] >= 4.5
        assert result["wcag_aa"]["passes"] is True
        assert result["wcag_aaa"]["passes"] is True

    def test_white_on_black_aa(self):
        result = srv.check_color_contrast("#FFFFFF", "#000000")
        assert result["contrast_ratio"] >= 4.5
        assert result["wcag_aa"]["passes"] is True

    def test_light_gray_on_white_fails(self):
        result = srv.check_color_contrast("#CCCCCC", "#FFFFFF")
        assert result["wcag_aa"]["passes"] is False

    def test_large_text_lower_threshold(self):
        result_normal = srv.check_color_contrast("#666666", "#FFFFFF", font_size=14.0)
        result_large = srv.check_color_contrast("#666666", "#FFFFFF", font_size=24.0)
        assert result_large["is_large_text"] is True
        if not result_normal["wcag_aa"]["passes"]:
            assert result_large["wcag_aa"]["required"] < result_normal["wcag_aa"]["required"]

    def test_bold_large_text(self):
        result = srv.check_color_contrast("#666666", "#FFFFFF", font_size=18.66, bold=True)
        assert result["is_large_text"] is True

    def test_normal_text_not_large(self):
        result = srv.check_color_contrast("#000000", "#FFFFFF", font_size=16.0)
        assert result["is_large_text"] is False

    def test_invalid_hex_color(self):
        result = srv.check_color_contrast("not-a-color", "#FFFFFF")
        assert "error" in result

    def test_result_keys(self):
        result = srv.check_color_contrast("#333333", "#FFFFFF")
        assert "contrast_ratio" in result
        assert "foreground" in result
        assert "background" in result
        assert "wcag_aa" in result
        assert "wcag_aaa" in result

    def test_custom_colors(self):
        result = srv.check_color_contrast("#1A5276", "#AED6F1")
        assert "contrast_ratio" in result
        assert result["contrast_ratio"] > 1.0


class TestSuggestAltText:
    def test_photo_type(self):
        result = srv.suggest_alt_text("A sunset over the ocean", image_type="photo")
        assert result["suggested_alt_text"] == "Photo of A sunset over the ocean"
        assert result["image_type"] == "photo"
        assert result["wcag_reference"] == "WCAG 2.1 - 1.1.1 Non-text Content (Level A)"

    def test_icon_type(self):
        result = srv.suggest_alt_text("Search", image_type="icon")
        assert result["max_recommended_length"] == 50
        assert len(result["tips"]) > 0

    def test_chart_type(self):
        result = srv.suggest_alt_text("Revenue growth over 5 years", image_type="chart")
        assert "Chart" in result["suggested_alt_text"]
        assert result["max_recommended_length"] == 250

    def test_decorative_type(self):
        result = srv.suggest_alt_text("Decorative border", image_type="decorative")
        assert result["suggested_alt_text"] == ""
        assert result["max_recommended_length"] == 0

    def test_logo_type(self):
        result = srv.suggest_alt_text("Acme Corp", image_type="logo")
        assert "Acme Corp" in result["suggested_alt_text"]

    def test_screenshot_type(self):
        result = srv.suggest_alt_text("Dashboard settings page", image_type="screenshot")
        assert "Screenshot" in result["suggested_alt_text"]

    def test_diagram_type(self):
        result = srv.suggest_alt_text("Microservices architecture flow", image_type="diagram")
        assert "Diagram" in result["suggested_alt_text"]

    def test_unknown_type_defaults_photo(self):
        result = srv.suggest_alt_text("Something", image_type="unknown_type")
        assert result["image_type"] == "photo"

    def test_tips_always_present(self):
        for img_type in ["photo", "icon", "chart", "logo", "screenshot", "diagram"]:
            result = srv.suggest_alt_text("Test", image_type=img_type)
            assert isinstance(result["tips"], list)


class TestCheckHeadingHierarchy:
    def test_valid_hierarchy(self):
        html = "<h1>Title</h1><h2>Section</h2><h3>Subsection</h3>"
        result = srv.check_heading_hierarchy(html)
        assert result["valid"] is True
        assert result["heading_count"] == 3

    def test_no_h1(self):
        html = "<h2>Section</h2><h3>Sub</h3>"
        result = srv.check_heading_hierarchy(html)
        assert result["valid"] is False
        assert any(i["issue"] == "No h1 heading found" for i in result["issues"])

    def test_multiple_h1(self):
        html = "<h1>First</h1><h1>Second</h1>"
        result = srv.check_heading_hierarchy(html)
        assert any("Multiple h1" in i["issue"] for i in result["issues"])

    def test_skipped_level(self):
        html = "<h1>Title</h1><h3>Skipped h2</h3>"
        result = srv.check_heading_hierarchy(html)
        assert result["valid"] is False
        assert any("Skipped heading level" in i["issue"] for i in result["issues"])

    def test_empty_html(self):
        result = srv.check_heading_hierarchy("<p>No headings</p>")
        assert result["heading_count"] == 0
        assert any("No h1" in i["issue"] for i in result["issues"])

    def test_first_heading_not_h1(self):
        html = "<h2>Starts with h2</h2>"
        result = srv.check_heading_hierarchy(html)
        assert any(i["severity"] == "error" for i in result["issues"])


class TestAriaValidator:
    def test_valid_role(self):
        html = '<div role="button">Click me</div>'
        result = srv.aria_validator(html)
        assert result["valid"] is True

    def test_invalid_role(self):
        html = '<div role="fake_role">Bad</div>'
        result = srv.aria_validator(html)
        assert result["valid"] is False
        assert any("Invalid ARIA role" in i["issue"] for i in result["issues"])

    def test_aria_label_without_role(self):
        html = '<div aria-label="Menu">Items</div>'
        result = srv.aria_validator(html)
        assert any("aria-label but no role" in i["issue"] for i in result["issues"])

    def test_aria_hidden_on_focusable(self):
        html = '<button aria-hidden="true">Hidden button</button>'
        result = srv.aria_validator(html)
        assert any("aria-hidden" in i["issue"] for i in result["issues"])

    def test_clean_html_passes(self):
        html = '<div role="navigation"><ul role="menu"><li role="menuitem">Item</li></ul></div>'
        result = srv.aria_validator(html)
        assert result["valid"] is True

    def test_counts_aria_attributes(self):
        html = '<div role="button" aria-label="Click" aria-expanded="true">Text</div>'
        result = srv.aria_validator(html)
        assert result["aria_attributes_found"] >= 2
        assert result["roles_found"] >= 1

    def test_empty_html(self):
        result = srv.aria_validator("<p>Just a paragraph</p>")
        assert result["valid"] is True
        assert result["issue_count"] == 0