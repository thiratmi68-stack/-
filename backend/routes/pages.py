from flask import Blueprint, send_from_directory, current_app
import os

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/admin')
def admin_page():
    # Use current_app.root_path (which is backend/) to find ../Page
    page_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'Page'))
    return send_from_directory(page_dir, 'admin.html')

@pages_bp.route('/admin/')
def admin_page_slash():
    page_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'Page'))
    return send_from_directory(page_dir, 'admin.html')

@pages_bp.route('/admin.html')
def admin_page_file():
    page_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'Page'))
    return send_from_directory(page_dir, 'admin.html')

# Catch-all
@pages_bp.route('/', defaults={'path': 'index.html'})
@pages_bp.route('/<path:path>')
def serve_page(path):
    page_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'Page'))
    target = os.path.join(page_dir, path)
    if os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(page_dir, path)
    return send_from_directory(page_dir, 'index.html')
