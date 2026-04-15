# Accessibility AI MCP Server

> By [MEOK AI Labs](https://meok.ai) — Web accessibility (a11y) checking tools for WCAG 2.1 compliance

## Installation

```bash
pip install accessibility-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install accessibility-ai-mcp
```

## Tools

### `check_color_contrast`
Check WCAG 2.1 color contrast ratio between foreground and background colors. Returns AA/AAA pass/fail for normal and large text.

**Parameters:**
- `foreground` (str): Foreground/text color in hex (e.g., '#333333')
- `background` (str): Background color in hex (e.g., '#FFFFFF')
- `font_size` (float): Font size in pixels (default 16)
- `bold` (bool): Whether text is bold (default False)

### `suggest_alt_text`
Suggest alt text guidelines and templates for different image types per WCAG 2.1 - 1.1.1 Non-text Content.

**Parameters:**
- `context` (str): Description of the image content/context
- `image_type` (str): Image type — 'photo', 'icon', 'chart', 'decorative', 'logo', 'screenshot', 'diagram'

### `check_heading_hierarchy`
Check heading hierarchy in HTML for proper nesting (h1 -> h2 -> h3...) per WCAG 1.3.1.

**Parameters:**
- `html` (str): HTML content to analyze

### `aria_validator`
Validate ARIA attributes and roles in HTML for correctness. Checks for invalid roles, missing role attributes, and focusable elements with aria-hidden.

**Parameters:**
- `html` (str): HTML content to validate

## Authentication

Free tier: 50 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs
