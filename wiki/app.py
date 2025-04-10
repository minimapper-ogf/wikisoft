from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from utils import get_page_path, list_pages, search_pages, get_page_info, markdown_to_html, list_pages_by_category
import os
from fuzzywuzzy import fuzz, process

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/media'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

DATA_DIR = "data/pages"
MEDIA_DIR = "data/media"

def get_all_pages():
    """Get all page titles from the data/pages directory."""
    pages = []
    for filename in os.listdir(DATA_DIR):
        # Look for .txt files instead of .md
        if filename.endswith(".txt"):  # Ensure the correct file type
            page_title = filename[:-4]  # Remove the '.txt' extension to get the title
            pages.append(page_title)
    return pages


@app.route('/')
def home():
    return redirect(url_for('view_page', title="Main Page"))

@app.route('/wiki/<title>')
def view_page(title):
    try:
        with open(get_page_path(title), 'r', encoding='utf-8') as f:
            content = f.read()
        content, toc, categories = markdown_to_html(content)  # Get content, TOC, and categories
    except FileNotFoundError:
        return redirect(url_for('edit_page', title=title))
    
    # Add categories to page context
    return render_template("view.html", title=title, content=content, toc=toc, categories=categories, pages=list_pages())

@app.route('/category/<category>')
def view_category(category):
    pages = list_pages_by_category(category)  # Get pages for the category
    return render_template("category_page.html", category=category, pages=pages)

@app.route('/edit/<title>', methods=['GET', 'POST'])
def edit_page(title):
    path = get_page_path(title)

    if request.method == 'POST':
        content = request.form['content'].replace('\r\n', '\n').strip() + '\n'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return redirect(url_for('view_page', title=title))

    content = ""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().replace('\r\n', '\n').strip()
    return render_template("edit.html", title=title, content=content)

@app.route('/pages')
def all_pages():
    pages = list_pages()
    return render_template("all_pages.html", pages=pages)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()  # Normalize query to lowercase
    all_pages = get_all_pages()  # Get all page titles
    
    # Use fuzzy search to match the query with page titles
    results = process.extract(query, all_pages, limit=10, scorer=fuzz.partial_ratio)

    # Sort results by score (highest first)
    results = sorted(results, key=lambda x: x[1], reverse=True)

    return render_template('search_results.html', query=query, results=results)

@app.route('/upload', methods=['GET', 'POST'])
def upload_media():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(save_path)
            return redirect(url_for('upload_media'))
    return render_template('upload.html')

@app.route('/media/<filename>')
def serve_media(filename):
    return send_from_directory(MEDIA_DIR, filename)

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
