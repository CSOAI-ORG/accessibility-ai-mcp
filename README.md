<div align="center">

# Accessibility Ai MCP

**Accessibility AI MCP Server**

[![PyPI](https://img.shields.io/pypi/v/meok-accessibility-ai-mcp)](https://pypi.org/project/meok-accessibility-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Accessibility AI MCP Server
Web accessibility (a11y) checking tools powered by MEOK AI Labs.

## Tools

| Tool | Description |
|------|-------------|
| `check_color_contrast` | Check WCAG 2.1 color contrast ratio between foreground and background colors. |
| `suggest_alt_text` | Suggest alt text guidelines and templates for different image types. |
| `check_heading_hierarchy` | Check heading hierarchy in HTML for proper nesting (h1 -> h2 -> h3...). |
| `aria_validator` | Validate ARIA attributes and roles in HTML for correctness. |

## Installation

```bash
pip install meok-accessibility-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "accessibility-ai": {
      "command": "python",
      "args": ["-m", "meok_accessibility_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
