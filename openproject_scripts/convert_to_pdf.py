#!/usr/bin/env python3
"""
Convert WORK_PACKAGES_REFERENCE.md to PDF
Uses markdown2html + wkhtmltopdf or similar
"""

import subprocess
import os
import sys

INPUT_FILE = "/opt/localaddons/WORK_PACKAGES_REFERENCE.md"
OUTPUT_PDF = "/opt/localaddons/WORK_PACKAGES_REFERENCE.pdf"
TEMP_HTML = "/tmp/work_packages.html"

def check_tool(tool_name):
    """Check if a command-line tool is available"""
    try:
        subprocess.run([tool_name, "--version"], 
                      capture_output=True, 
                      timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def convert_md_to_html(md_file, html_file):
    """Convert markdown to HTML"""
    print(f"Reading markdown from: {md_file}")
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Simple HTML template with styling
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Odoo 19 HR Security Enhancement - Work Packages Reference</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        strong {{
            color: #2c3e50;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-left: 4px solid #3498db;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 30px 0;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        .status-closed {{
            color: #27ae60;
            font-weight: bold;
        }}
    </style>
</head>
<body>
{content}
</body>
</html>"""
    
    # Convert markdown to HTML (basic conversion)
    html_content = md_content
    
    # Convert markdown headers
    html_content = html_content.replace('# ', '<h1>')
    html_content = html_content.replace('\n## ', '</p>\n<h2>')
    html_content = html_content.replace('\n### ', '</p>\n<h3>')
    
    # Convert bold text
    import re
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
    
    # Convert code blocks
    html_content = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code>\2</code></pre>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_content)
    
    # Convert lists
    lines = html_content.split('\n')
    in_list = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            new_lines.append('<li>' + line.strip()[2:] + '</li>')
        elif line.strip().startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
            if not in_list:
                new_lines.append('<ol>')
                in_list = True
            new_lines.append('<li>' + line.strip()[3:] + '</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            if line.strip() and not line.startswith('<'):
                new_lines.append('<p>' + line + '</p>')
            else:
                new_lines.append(line)
    
    html_content = '\n'.join(new_lines)
    
    # Handle checkmarks
    html_content = html_content.replace('✅', '<span class="status-closed">✅</span>')
    
    # Create final HTML
    final_html = html_template.format(content=html_content)
    
    print(f"Writing HTML to: {html_file}")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    return html_file

def convert_html_to_pdf_wkhtmltopdf(html_file, pdf_file):
    """Convert HTML to PDF using wkhtmltopdf"""
    print("Converting HTML to PDF using wkhtmltopdf...")
    cmd = [
        'wkhtmltopdf',
        '--enable-local-file-access',
        '--page-size', 'A4',
        '--margin-top', '20mm',
        '--margin-bottom', '20mm',
        '--margin-left', '15mm',
        '--margin-right', '15mm',
        html_file,
        pdf_file
    ]
    subprocess.run(cmd, check=True)
    return pdf_file

def convert_html_to_pdf_weasyprint(html_file, pdf_file):
    """Convert HTML to PDF using WeasyPrint"""
    print("Converting HTML to PDF using WeasyPrint...")
    try:
        from weasyprint import HTML
        HTML(filename=html_file).write_pdf(pdf_file)
        return pdf_file
    except ImportError:
        print("WeasyPrint not available")
        return None

def convert_html_to_pdf_pandoc(html_file, pdf_file):
    """Convert HTML to PDF using pandoc"""
    print("Converting HTML to PDF using pandoc...")
    cmd = [
        'pandoc',
        html_file,
        '-o', pdf_file,
        '--pdf-engine=wkhtmltopdf',
        '-V', 'geometry:margin=1in'
    ]
    subprocess.run(cmd, check=True)
    return pdf_file

def main():
    print("="*60)
    print("Markdown to PDF Converter")
    print("="*60)
    print()
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return 1
    
    # Step 1: Convert markdown to HTML
    try:
        html_file = convert_md_to_html(INPUT_FILE, TEMP_HTML)
        print(f"✓ HTML created: {html_file}")
    except Exception as e:
        print(f"ERROR: Failed to convert MD to HTML: {e}")
        return 1
    
    # Step 2: Try different PDF converters
    pdf_created = False
    
    # Try wkhtmltopdf first
    if check_tool('wkhtmltopdf'):
        try:
            convert_html_to_pdf_wkhtmltopdf(html_file, OUTPUT_PDF)
            pdf_created = True
            print(f"✓ PDF created using wkhtmltopdf: {OUTPUT_PDF}")
        except Exception as e:
            print(f"wkhtmltopdf failed: {e}")
    
    # Try WeasyPrint
    if not pdf_created:
        try:
            if convert_html_to_pdf_weasyprint(html_file, OUTPUT_PDF):
                pdf_created = True
                print(f"✓ PDF created using WeasyPrint: {OUTPUT_PDF}")
        except Exception as e:
            print(f"WeasyPrint failed: {e}")
    
    # Try pandoc
    if not pdf_created and check_tool('pandoc'):
        try:
            convert_html_to_pdf_pandoc(html_file, OUTPUT_PDF)
            pdf_created = True
            print(f"✓ PDF created using pandoc: {OUTPUT_PDF}")
        except Exception as e:
            print(f"pandoc failed: {e}")
    
    if not pdf_created:
        print()
        print("="*60)
        print("NO PDF CONVERTER AVAILABLE")
        print("="*60)
        print()
        print("HTML file created instead: " + TEMP_HTML)
        print("You can:")
        print("  1. Open the HTML file in a browser and use Print to PDF")
        print("  2. Install one of these tools:")
        print("     - apt-get install wkhtmltopdf")
        print("     - pip3 install weasyprint")
        print("     - apt-get install pandoc")
        print()
        return 1
    
    print()
    print("="*60)
    print("SUCCESS!")
    print("="*60)
    print(f"PDF created: {OUTPUT_PDF}")
    print(f"File size: {os.path.getsize(OUTPUT_PDF):,} bytes")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
