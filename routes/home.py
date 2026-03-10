from flask import Blueprint, redirect, url_for
from flask_login import current_user

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    """
    Root route:
    - Authenticated users → dashboard
    - Guests → login
    """
    return (
        redirect(url_for("dashboard.index"))
        if current_user.is_authenticated
        else redirect(url_for("auth.login"))
    )