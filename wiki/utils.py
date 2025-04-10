import os

DATA_DIR = "data/pages"

def get_page_path(title):
    safe_title = title.replace(" ", "_")
    return os.path.join(DATA_DIR, f"{safe_title}.txt")

import re
import hashlib

def markdown_to_html(text):
    """Convert custom markdown to HTML."""
    toc = []  # List to store TOC entries
    def add_to_toc(header_text, level):
        toc.append((level, header_text))

    # Convert headers (e.g., # Header to <h1>Header</h1>)
    def replace_headers(m):
        level = len(m.group(1))  # Number of `#` symbols determines header level
        header_text = m.group(2)
        add_to_toc(header_text, level)
        return f"<h{level}>{header_text}</h{level}>"
    
    text = re.sub(r'^(#{1,6})\s*(.*)', replace_headers, text, flags=re.MULTILINE)

    # Convert bold (e.g., **bold** to <strong>bold</strong>)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Convert italics (e.g., *italic* to <em>italic</em>)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    # Convert unordered lists (e.g., - Item to <ul><li>Item</li></ul>)
    text = re.sub(r'^\s*[-*]\s*(.*)', r'<ul><li>\1</li></ul>', text, flags=re.MULTILINE)

    # Convert ordered lists (e.g., 1. Item to <ol><li>Item</li></ol>)
    text = re.sub(r'^\s*\d+\.\s*(.*)', r'<ol><li>\1</li></ol>', text, flags=re.MULTILINE)

    # Convert links (e.g., [text](url) to <a href="url">text</a>)
    text = re.sub(r'\[([^\]]+)\]\((.*?)\)', r'<a href="\2">\1</a>', text)

    # Convert custom image links ![[image.png]] to <img src="/media/image.png" alt="image">
    text = re.sub(
        r'!\[\[(.*?)\]\]',  # Custom image link syntax
        r'<img src="/media/\1" alt="\1" style="max-width: 100%; height: auto;">',  # Embed the image
        text
    )

    # Convert external image links (e.g., ![alt](http://example.com/image.png))
    text = re.sub(
        r'!\[([^\]]*)\]\((http[s]?://.*?)\)',  # Match external image URL
        r'<img src="\2" alt="\1" style="max-width: 100%; height: auto;">',  # Embed image
        text
    )

    # Convert custom audio links ![audiofile.mp3] to <audio controls>
    text = re.sub(
        r'!\[([^\]]*\.(mp3|wav|ogg))\]',  # Match audio file extensions (mp3, wav, ogg)
        r'<audio controls><source src="/media/\1" type="audio/\2">Your browser does not support the audio element.</audio>',
        text
    )

    # Convert custom table syntax {table}...{/table} to <table>...</table>
    text = re.sub(r'\{table\}(.*?)\{/table\}', lambda m: convert_table_to_html(m.group(1)), text, flags=re.DOTALL)

    # Convert plain text tables to HTML
    return text, toc

def convert_table_to_html(table_content):
    """Converts custom table content to HTML table."""
    # Clean the input table content, remove extra spaces and newlines
    table_content = re.sub(r'\n\s*\n', '\n', table_content.strip())

    rows = table_content.split('\n')
    html_table = "<table><thead><tr>"

    # Process the header row
    header_cells = rows[0].split('|')
    for cell in header_cells:
        html_table += f"<th>{cell.strip()}</th>"
    
    html_table += "</tr></thead><tbody>"

    # Process data rows
    for row in rows[1:]:
        html_table += "<tr>"
        data_cells = row.split('|')
        for cell in data_cells:
            html_table += f"<td>{cell.strip()}</td>"
        html_table += "</tr>"

    html_table += "</tbody></table>"
    return html_table

def parse_table(text):
    """Parse the table rows and format as <tr><td>."""
    rows = text.strip().split("\n")
    table_html = ""
    for row in rows:
        columns = row.split("|")
        table_html += "<tr>" + "".join(f"<td>{col.strip()}</td>" for col in columns[1:-1]) + "</tr>"
    return table_html

def generate_media_html(file_path):
    """
    Generate HTML for embedding media files based on their type.
    """
    if file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
        return f'<img src="{file_path}" alt="Image" />'
    elif file_path.endswith(('.mp3', '.wav', '.ogg')):
        return f'<audio controls><source src="{file_path}" type="audio/{file_path.split(".")[-1]}">Your browser does not support the audio element.</audio>'
    elif file_path.endswith(('.mp4', '.webm', '.ogg')):
        return f'<video controls><source src="{file_path}" type="video/{file_path.split(".")[-1]}">Your browser does not support the video element.</video>'
    else:
        return f'<a href="{file_path}">Download File</a>'

def list_pages():
    return [f[:-4].replace("_", " ") for f in os.listdir(DATA_DIR) if f.endswith(".txt")]

def search_pages(query):
    results = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".txt"):
            path = os.path.join(DATA_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                if query.lower() in f.read().lower():
                    results.append(filename[:-4].replace("_", " "))
    return results

def get_page_info(title):
    path = get_page_path(title)
    if os.path.exists(path):
        return {
            'size': os.path.getsize(path),
            'modified': os.path.getmtime(path),
        }
    return {}
