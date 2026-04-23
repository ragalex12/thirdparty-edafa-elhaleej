#!/usr/bin/env python3
"""Convert tester AR markdown to RTL HTML and invoke wkhtmltopdf (stdlib only)."""

import html
import re
import subprocess
import sys
from pathlib import Path


def inline_format(raw: str) -> str:
    parts = re.split(r"(\*\*.+?\*\*)", raw)
    out = []
    for p in parts:
        if len(p) >= 4 and p.startswith("**") and p.endswith("**"):
            out.append("<strong>%s</strong>" % html.escape(p[2:-2]))
        else:
            out.append(html.escape(p))
    return "".join(out)


def md_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    chunks = []
    in_ol = False
    in_ul = False

    def close_lists():
        nonlocal in_ol, in_ul
        s = ""
        if in_ul:
            s += "</ul>"
            in_ul = False
        if in_ol:
            s += "</ol>"
            in_ol = False
        return s

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "---":
            chunks.append(close_lists())
            chunks.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            chunks.append(close_lists())
            level = len(m.group(1))
            tag = "h1" if level == 1 else "h2" if level == 2 else "h3"
            chunks.append("<%s>%s</%s>" % (tag, inline_format(m.group(2)), tag))
            i += 1
            continue

        num = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if num:
            if in_ul:
                chunks.append("</ul>")
                in_ul = False
            if not in_ol:
                chunks.append("<ol>")
                in_ol = True
            chunks.append("<li>%s</li>" % inline_format(num.group(2)))
            i += 1
            continue

        if stripped.startswith("- "):
            if in_ol:
                chunks.append("</ol>")
                in_ol = False
            if not in_ul:
                chunks.append("<ul>")
                in_ul = True
            chunks.append("<li>%s</li>" % inline_format(stripped[2:]))
            i += 1
            continue

        chunks.append(close_lists())
        if stripped:
            chunks.append("<p>%s</p>" % inline_format(line))
        i += 1

    chunks.append(close_lists())
    body = "\n".join(chunks)

    return (
        "<!DOCTYPE html>\n<html dir=\"rtl\" lang=\"ar\">\n<head>\n"
        '<meta charset="utf-8"/>\n'
        "<title>وصف استخدام للمختبِرين</title>\n"
        "<style>\n"
        "body { font-family: 'DejaVu Sans', 'Noto Sans Arabic', Arial, sans-serif; "
        "margin: 24px; line-height: 1.65; font-size: 11pt; color: #222; }\n"
        "h1 { font-size: 18pt; border-bottom: 1px solid #ccc; padding-bottom: 6px; }\n"
        "h2 { font-size: 14pt; margin-top: 18px; color: #1a1a1a; }\n"
        "h3 { font-size: 12pt; margin-top: 12px; }\n"
        "p { margin: 8px 0; }\n"
        "ul, ol { margin: 8px 0 8px 0; padding-right: 24px; }\n"
        "li { margin: 4px 0; }\n"
        "hr { border: none; border-top: 1px solid #ddd; margin: 16px 0; }\n"
        "</style>\n</head>\n<body>\n"
        + body
        + "\n</body>\n</html>"
    )


def main():
    if len(sys.argv) < 3:
        print("Usage: md_to_pdf_ar.py INPUT.md OUTPUT.pdf", file=sys.stderr)
        sys.exit(1)
    md_path = Path(sys.argv[1])
    pdf_path = Path(sys.argv[2])
    md_text = md_path.read_text(encoding="utf-8")
    html_text = md_to_html(md_text)
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(html_text, encoding="utf-8")
    cmd = [
        "wkhtmltopdf",
        "--encoding",
        "utf-8",
        "--enable-local-file-access",
        "--quiet",
        str(html_path),
        str(pdf_path),
    ]
    subprocess.run(cmd, check=True)
    print("Wrote:", pdf_path)


if __name__ == "__main__":
    main()
