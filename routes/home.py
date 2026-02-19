from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    """Home page - redirects based on authentication status"""
    if current_user.is_authenticated:
        # Redirect authenticated users to their dashboard
        return redirect(url_for('dashboard.index'))
    else:
        # Redirect unauthenticated users to login
        return redirect(url_for('auth.login'))