#!/usr/bin/env python
"""Convert Markdown policy memo to PDF with improved formatting"""

import subprocess
import sys
import os
import re

def install_package(package):
    """Install a package using pip"""
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])

def convert_with_reportlab():
    """Convert using markdown + reportlab with better table and formatting support"""
    try:
        print("Installing required packages...")
        install_package('markdown')
        install_package('reportlab')
        
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        import os.path
        
        print("Reading markdown file...")
        with open('documentation/Rough_Draft_Policy_Memo.md', 'r', encoding='utf-8') as f:
            md_text = f.read()
        
        print("Creating PDF...")
        # Create PDF
        doc = SimpleDocTemplate(
            'documentation/Rough_Draft_Policy_Memo.pdf',
            pagesize=letter,
            rightMargin=60,
            leftMargin=60,
            topMargin=60,
            bottomMargin=40
        )
        
        # Container for content
        elements = []
        
        # Define styles - Academic paper style with Times New Roman
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='Times-Bold',
            fontSize=16,
            textColor=colors.black,
            spaceAfter=12,
            spaceBefore=6,
            alignment=TA_LEFT
        )
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontName='Times-Bold',
            fontSize=13,
            textColor=colors.black,
            spaceAfter=10,
            spaceBefore=16,
            alignment=TA_LEFT
        )
        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontName='Times-Bold',
            fontSize=12,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT
        )
        h4_style = ParagraphStyle(
            'CustomH4',
            parent=styles['Heading4'],
            fontName='Times-Bold',
            fontSize=11,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=10,
            alignment=TA_LEFT
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['BodyText'],
            fontName='Times-Roman',
            fontSize=11,
            leading=15,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            textColor=colors.black
        )
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=normal_style,
            fontName='Times-Roman',
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4
        )
        code_style = ParagraphStyle(
            'Code',
            parent=styles['Code'],
            fontSize=9,
            fontName='Courier',
            backColor=colors.HexColor('#f9f9f9'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.black,
            borderWidth=0.5,
            borderColor=colors.grey,
            borderPadding=8
        )
        
        def clean_unicode_subscripts(text):
            """Convert unicode subscripts to regular characters"""
            subscript_map = {
                '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
                '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
                'ₐ': 'a', 'ₑ': 'e', 'ₒ': 'o', 'ₓ': 'x', 'ₙ': 'n',
                'ₜ': 't', 'ᵢ': 'i', 'ⱼ': 'j', 'ₖ': 'k', 'ₘ': 'm',
                'ₚ': 'p', 'ₛ': 's', 'ᵤ': 'u', 'ᵥ': 'v', 'ᵣ': 'r',
                'ₗ': 'l', 'ₕ': 'h', 'ₖ': 'k', 'ᵦ': 'b', 'ᵧ': 'g',
                'ᵨ': 'r', 'ᵩ': 'f', 'ᵪ': 'x'
            }
            for uni, normal in subscript_map.items():
                text = text.replace(uni, normal)
            return text
        
        def extract_images(text):
            """Extract image references from markdown"""
            # Find all image markdown: ![alt](path)
            pattern = r'!\[(.*?)\]\((.*?)\)'
            return re.findall(pattern, text)
        
        def format_text(text, is_code=False):
            """Format markdown text to reportlab HTML"""
            if not text:
                return ""
            
            # Handle escaped characters FIRST, before any other processing
            text = text.replace('\\*', '☆ESCAPED_ASTERISK☆')  # Temporarily replace escaped asterisks
            text = text.replace('\\\\', '☆ESCAPED_BACKSLASH☆')  # Temporarily replace escaped backslashes
            
            # For code blocks, just clean unicode and escape
            if is_code:
                text = clean_unicode_subscripts(text)
                text = text.replace('&', '&amp;')
                text = text.replace('<', '&lt;').replace('>', '&gt;')
                text = text.replace('×', 'x')
                # Restore escaped characters
                text = text.replace('☆ESCAPED_ASTERISK☆', '*')
                text = text.replace('☆ESCAPED_BACKSLASH☆', '\\')
                return text
            
            # Remove image markdown syntax (we'll handle images separately)
            text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
            
            # Convert unicode subscripts to readable text
            text = clean_unicode_subscripts(text)
            
            # Convert underscore subscripts to readable format
            text = re.sub(r'([a-zA-Z]+)_([a-zA-Z0-9]+)', r'\1_\2', text)
            
            # Handle multiplication sign
            text = text.replace('×', 'x')
            
            # Now handle markdown formatting BEFORE escaping
            # Handle triple asterisks first (bold + italic)
            text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<<<BOLDITALIC>>>\1<<<ENDBOLDITALIC>>>', text)
            # Handle double asterisks (bold)
            text = re.sub(r'\*\*(.+?)\*\*', r'<<<BOLD>>>\1<<<ENDBOLD>>>', text)
            # Handle single asterisks (italic) - but not if it's a bullet
            text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'<<<ITALIC>>>\1<<<ENDITALIC>>>', text)
            # Handle inline code
            text = re.sub(r'`(.+?)`', r'<<<CODE>>>\1<<<ENDCODE>>>', text)
            
            # Now escape special XML characters
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;').replace('>', '&gt;')
            
            # Restore formatting with proper HTML tags
            text = text.replace('&lt;&lt;&lt;BOLDITALIC&gt;&gt;&gt;', '<b><i>')
            text = text.replace('&lt;&lt;&lt;ENDBOLDITALIC&gt;&gt;&gt;', '</i></b>')
            text = text.replace('&lt;&lt;&lt;BOLD&gt;&gt;&gt;', '<b>')
            text = text.replace('&lt;&lt;&lt;ENDBOLD&gt;&gt;&gt;', '</b>')
            text = text.replace('&lt;&lt;&lt;ITALIC&gt;&gt;&gt;', '<i>')
            text = text.replace('&lt;&lt;&lt;ENDITALIC&gt;&gt;&gt;', '</i>')
            text = text.replace('&lt;&lt;&lt;CODE&gt;&gt;&gt;', '<font name="Courier">')
            text = text.replace('&lt;&lt;&lt;ENDCODE&gt;&gt;&gt;', '</font>')
            
            # Restore escaped characters as literal characters
            text = text.replace('☆ESCAPED_ASTERISK☆', '*')
            text = text.replace('☆ESCAPED_BACKSLASH☆', '\\')
            
            return text
        
        def parse_table(lines, start_idx):
            """Parse markdown table and return Table object and next line index"""
            table_lines = []
            i = start_idx
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            
            if len(table_lines) < 2:
                return None, start_idx + 1
            
            # Parse table
            data = []
            for line in table_lines:
                # Skip separator line
                if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                    continue
                cells = [cell.strip() for cell in line.strip().split('|')[1:-1]]
                # Format each cell
                formatted_cells = [Paragraph(format_text(cell), normal_style) for cell in cells]
                data.append(formatted_cells)
            
            if not data:
                return None, i
            
            # Create table with styling - Academic paper style
            table = Table(data, colWidths=[doc.width / len(data[0])] * len(data[0]))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            return table, i
        
        # Parse markdown
        lines = md_text.split('\n')
        i = 0
        in_code_block = False
        code_buffer = []
        
        while i < len(lines):
            line = lines[i]
            
            # Handle code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    if code_buffer:
                        code_text = '\n'.join(code_buffer)
                        # Clean the code text properly
                        code_text = format_text(code_text, is_code=True)
                        code_para = Paragraph(code_text.replace('\n', '<br/>'), code_style)
                        elements.append(code_para)
                        elements.append(Spacer(1, 8))
                        code_buffer = []
                    in_code_block = False
                else:
                    in_code_block = True
                i += 1
                continue
            
            if in_code_block:
                code_buffer.append(line)
                i += 1
                continue
            
            line_stripped = line.strip()
            
            # Empty line
            if not line_stripped:
                elements.append(Spacer(1, 4))
                i += 1
                continue
            
            # Headers
            if line_stripped.startswith('#### '):
                text = format_text(line_stripped[5:].strip())
                elements.append(Paragraph(text, h4_style))
                i += 1
            elif line_stripped.startswith('### '):
                text = format_text(line_stripped[4:].strip())
                elements.append(Paragraph(text, h3_style))
                i += 1
            elif line_stripped.startswith('## '):
                text = format_text(line_stripped[3:].strip())
                # Add page break before introduction, references, and appendix
                if any(keyword in text.lower() for keyword in ['introduction', 'references', 'appendix']):
                    if elements:  # Don't add page break at the very beginning
                        elements.append(PageBreak())
                elements.append(Paragraph(text, h2_style))
                i += 1
            elif line_stripped.startswith('# '):
                text = format_text(line_stripped[2:].strip())
                elements.append(Paragraph(text, title_style))
                i += 1
            # Horizontal rule
            elif line_stripped.startswith('---'):
                elements.append(Spacer(1, 10))
                i += 1
            # Tables
            elif line_stripped.startswith('|'):
                table, next_i = parse_table(lines, i)
                if table:
                    elements.append(Spacer(1, 6))
                    elements.append(table)
                    elements.append(Spacer(1, 10))
                i = next_i
            # List items
            elif line_stripped.startswith('- ') or (line_stripped.startswith('* ') and not line_stripped.startswith('**')):
                text = format_text(line_stripped[2:].strip())
                elements.append(Paragraph('• ' + text, bullet_style))
                i += 1
            elif re.match(r'^\d+\.\s', line_stripped):
                text = format_text(re.sub(r'^\d+\.\s', '', line_stripped))
                num = re.match(r'^(\d+)\.', line_stripped).group(1)
                elements.append(Paragraph(f'{num}. {text}', bullet_style))
                i += 1
            # Regular paragraph
            else:
                # Check for images in the line
                images = extract_images(line_stripped)
                if images:
                    for alt_text, img_path in images:
                        # Convert relative path to absolute
                        if img_path.startswith('../'):
                            img_path = img_path.replace('../', 'c:/Users/LENOVO/Desktop/Duke/PDS - 720/pds-2025-opioids-dat-a/')
                        
                        # Check if image exists
                        if os.path.exists(img_path):
                            try:
                                # Add image with caption - preserve aspect ratio
                                img = Image(img_path)
                                # Scale to fit page width while maintaining aspect ratio
                                img_width = 6.5*inch  # Page width minus margins
                                aspect = img.imageHeight / float(img.imageWidth)
                                img.drawHeight = img_width * aspect
                                img.drawWidth = img_width
                                elements.append(Spacer(1, 10))
                                elements.append(img)
                                if alt_text:
                                    caption_style = ParagraphStyle(
                                        'Caption',
                                        parent=normal_style,
                                        fontSize=9,
                                        alignment=TA_CENTER,
                                        textColor=colors.grey
                                    )
                                    elements.append(Paragraph(f'<i>{alt_text}</i>', caption_style))
                                elements.append(Spacer(1, 10))
                            except Exception as e:
                                # If image fails, add a note
                                elements.append(Paragraph(f'[Image: {alt_text}]', normal_style))
                    i += 1
                else:
                    text = format_text(line_stripped)
                    if text:
                        elements.append(Paragraph(text, normal_style))
                    i += 1
        
        # Build PDF
        doc.build(elements)
        print('\n✓ PDF created successfully: documentation/Rough_Draft_Policy_Memo.pdf')
        
        # Get file size
        size = os.path.getsize('documentation/Rough_Draft_Policy_Memo.pdf')
        print(f'  File size: {size:,} bytes ({size/1024:.1f} KB)')
        
        return True
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Converting Markdown to PDF")
    print("=" * 60)
    
    success = convert_with_reportlab()
    
    if not success:
        print("\n❌ Conversion failed.")
        print("\nAlternative options:")
        print("1. Install pandoc: https://pandoc.org/installing.html")
        print("2. Use online converter: https://www.markdowntopdf.com/")
        print("3. Open in VS Code and use 'Markdown PDF' extension")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Conversion complete!")
    print("=" * 60)
