"""
Accessibility AI MCP Server
Web accessibility (a11y) checking tools powered by MEOK AI Labs.
"""


import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import re
import time
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("accessibility-ai", instructions="MEOK AI Labs MCP Server")

_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 50
WINDOW = 86400


def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day. Upgrade at https://meok.ai/pricing")
    _call_counts[tool_name].append(now)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _relative_luminance(r: int, g: int, b: int) -> float:
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


@mcp.tool()
def check_color_contrast(foreground: str, background: str, font_size: float = 16.0, bold: bool = False, api_key: str = "") -> dict:
    """Check WCAG 2.1 color contrast ratio between foreground and background colors.

    Args:
        foreground: Foreground/text color in hex (e.g., '#333333')
        background: Background color in hex (e.g., '#FFFFFF')
        font_size: Font size in pixels (default 16)
        bold: Whether text is bold (default False)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("check_color_contrast")
    try:
        fg_rgb = _hex_to_rgb(foreground)
        bg_rgb = _hex_to_rgb(background)
    except (ValueError, IndexError):
        return {"error": "Invalid hex color. Use format #RGB or #RRGGBB"}
    l1 = _relative_luminance(*fg_rgb)
    l2 = _relative_luminance(*bg_rgb)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)
    is_large = font_size >= 24 or (font_size >= 18.66 and bold)
    aa_normal = ratio >= 4.5
    aa_large = ratio >= 3.0
    aaa_normal = ratio >= 7.0
    aaa_large = ratio >= 4.5
    passes_aa = aa_large if is_large else aa_normal
    passes_aaa = aaa_large if is_large else aaa_normal
    return {"contrast_ratio": round(ratio, 2), "foreground": foreground, "background": background,
            "wcag_aa": {"passes": passes_aa, "required": 3.0 if is_large else 4.5},
            "wcag_aaa": {"passes": passes_aaa, "required": 4.5 if is_large else 7.0},
            "is_large_text": is_large, "font_size": font_size, "bold": bold}


@mcp.tool()
def suggest_alt_text(context: str, image_type: str = "photo", api_key: str = "") -> dict:
    """Suggest alt text guidelines and templates for different image types.

    Args:
        context: Description of the image content/context
        image_type: Image type - 'photo', 'icon', 'chart', 'decorative', 'logo', 'screenshot', 'diagram'
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("suggest_alt_text")
    guidelines = {
        "photo": {"template": f"Photo of {context}", "max_length": 125,
                  "tips": ["Describe the main subject and action", "Include relevant details (setting, emotion)",
                           "Don't start with 'Image of' or 'Picture of'"]},
        "icon": {"template": f"{context}" if context else "Icon", "max_length": 50,
                 "tips": ["Describe the icon's function, not appearance", "E.g., 'Search' not 'Magnifying glass icon'"]},
        "chart": {"template": f"Chart showing {context}", "max_length": 250,
                  "tips": ["Describe the data trend or key takeaway", "Include data type and axis labels",
                           "Provide a data table as alternative"]},
        "decorative": {"template": "", "max_length": 0,
                       "tips": ["Use empty alt='' for decorative images", "Use role='presentation' or aria-hidden='true'"]},
        "logo": {"template": f"{context} logo", "max_length": 50,
                 "tips": ["Use the company/brand name", "If it links, describe the destination"]},
        "screenshot": {"template": f"Screenshot of {context}", "max_length": 200,
                       "tips": ["Describe the key content shown", "Include any important text visible"]},
        "diagram": {"template": f"Diagram illustrating {context}", "max_length": 250,
                    "tips": ["Describe the relationships or flow", "Provide a text description as alternative"]},
    }
    guide = guidelines.get(image_type, guidelines["photo"])
    return {"suggested_alt_text": guide["template"], "image_type": image_type,
            "max_recommended_length": guide["max_length"], "tips": guide["tips"],
            "wcag_reference": "WCAG 2.1 - 1.1.1 Non-text Content (Level A)"}


@mcp.tool()
def check_heading_hierarchy(html: str, api_key: str = "") -> dict:
    """Check heading hierarchy in HTML for proper nesting (h1 -> h2 -> h3...).

    Args:
        html: HTML content to analyze
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("check_heading_hierarchy")
    headings = []
    for match in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', html, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1))
        text = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        headings.append({"level": level, "text": text[:80]})
    issues = []
    h1_count = sum(1 for h in headings if h["level"] == 1)
    if h1_count == 0:
        issues.append({"issue": "No h1 heading found", "severity": "error", "wcag": "1.3.1"})
    elif h1_count > 1:
        issues.append({"issue": f"Multiple h1 headings ({h1_count})", "severity": "warning", "wcag": "1.3.1"})
    if headings and headings[0]["level"] != 1:
        issues.append({"issue": f"First heading is h{headings[0]['level']}, should be h1", "severity": "error", "wcag": "1.3.1"})
    for i in range(1, len(headings)):
        if headings[i]["level"] > headings[i-1]["level"] + 1:
            issues.append({"issue": f"Skipped heading level: h{headings[i-1]['level']} -> h{headings[i]['level']} ('{headings[i]['text']}')",
                           "severity": "error", "wcag": "1.3.1"})
    return {"headings": headings, "heading_count": len(headings), "issues": issues,
            "valid": len([i for i in issues if i["severity"] == "error"]) == 0}


@mcp.tool()
def aria_validator(html: str, api_key: str = "") -> dict:
    """Validate ARIA attributes and roles in HTML for correctness.

    Args:
        html: HTML content to validate
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("aria_validator")
    valid_roles = {"alert", "alertdialog", "application", "article", "banner", "button", "cell",
                   "checkbox", "columnheader", "combobox", "complementary", "contentinfo", "definition",
                   "dialog", "directory", "document", "feed", "figure", "form", "grid", "gridcell",
                   "group", "heading", "img", "link", "list", "listbox", "listitem", "log", "main",
                   "marquee", "math", "menu", "menubar", "menuitem", "menuitemcheckbox", "menuitemradio",
                   "navigation", "none", "note", "option", "presentation", "progressbar", "radio",
                   "radiogroup", "region", "row", "rowgroup", "rowheader", "scrollbar", "search",
                   "searchbox", "separator", "slider", "spinbutton", "status", "switch", "tab",
                   "table", "tablist", "tabpanel", "term", "textbox", "timer", "toolbar", "tooltip",
                   "tree", "treegrid", "treeitem"}
    issues = []
    # Check roles
    for match in re.finditer(r'role=["\']([^"\']+)["\']', html, re.IGNORECASE):
        role = match.group(1)
        if role not in valid_roles:
            issues.append({"issue": f"Invalid ARIA role: '{role}'", "severity": "error"})
    # Check aria-label without role
    for match in re.finditer(r'<(\w+)\s[^>]*aria-label=["\'][^"\']+["\'][^>]*>', html, re.IGNORECASE):
        tag = match.group(1).lower()
        if tag in ('div', 'span') and 'role=' not in match.group(0).lower():
            issues.append({"issue": f"<{tag}> has aria-label but no role", "severity": "warning"})
    # Check aria-hidden on focusable
    for match in re.finditer(r'<(a|button|input|select|textarea)\s[^>]*aria-hidden=["\']true["\']', html, re.IGNORECASE):
        issues.append({"issue": f"Focusable element <{match.group(1)}> has aria-hidden='true'", "severity": "error"})
    # Count ARIA attributes
    aria_count = len(re.findall(r'aria-\w+', html))
    role_count = len(re.findall(r'role=', html))
    return {"issues": issues, "issue_count": len(issues), "aria_attributes_found": aria_count,
            "roles_found": role_count, "valid": not any(i["severity"] == "error" for i in issues)}


if __name__ == "__main__":
    mcp.run()
