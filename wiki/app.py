from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
from utils import get_page_path, list_pages, search_pages, get_page_info, markdown_to_html, list_pages_by_category
from fuzzywuzzy import fuzz, process
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import json

app = Flask(__name__)
app.secret_key = 'CREATE KEY WHEN  MAKING WIKI'  # Required for sessions
app.config['UPLOAD_FOLDER'] = 'data/media'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

DATA_DIR = "data/pages"
MEDIA_DIR = "data/media"
USERS_FILE = "data/users.json"

# ------------------ Account Helpers ------------------

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def authenticate(username, password):
    users = load_users()
    user = users.get(username)
    if user and check_password_hash(user['password_hash'], password):
        return True
    return False

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


# ------------------ Routes ------------------

@app.route('/')
def home():
    return redirect(url_for('view_page', title="Main Page"))

@app.route('/wiki/<title>')
def view_page(title):
    try:
        with open(get_page_path(title), 'r', encoding='utf-8') as f:
            content = f.read()
        content, toc, categories = markdown_to_html(content)
    except FileNotFoundError:
        return redirect(url_for('edit_page', title=title))
    
    return render_template("view.html", title=title, content=content, toc=toc, categories=categories, pages=list_pages())

@app.route('/category/<category>')
def view_category(category):
    pages = list_pages_by_category(category)
    return render_template("category_page.html", category=category, pages=pages)

@app.route('/edit/<title>', methods=['GET', 'POST'])
@login_required
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
    query = request.args.get('query', '').lower()
    all_pages = [p.lower() for p in get_all_pages()]
    results = process.extract(query, all_pages, limit=10, scorer=fuzz.partial_ratio)
    results = sorted(results, key=lambda x: x[1], reverse=True)
    return render_template('search_results.html', query=query, results=results)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users:
            flash("Username already exists. Choose another one.", "danger")
            return redirect(url_for('signup'))

        users[username] = {
            'password_hash': generate_password_hash(password)
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)

        session['username'] = username
        flash("Account created and logged in!", "success")
        return redirect(url_for('home'))

    return render_template("signup.html")


# ------------------ Auth Routes ------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate(username, password):
            session['username'] = username
            flash("Logged in successfully!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for('login'))

# ------------------ Startup ------------------

def get_all_pages():
    pages = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".txt"):
            pages.append(filename[:-4])
    return pages

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if not os.path.exists(USERS_FILE):
        # Optional: create default admin
        with open(USERS_FILE, "w") as f:
            json.dump({}, f, indent=2)
    app.run(debug=True)
