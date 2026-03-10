from urllib.parse import urlparse, urljoin

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User
from forms import LoginForm, RegistrationForm

auth_bp = Blueprint("auth", __name__)


def is_safe_url(target: str) -> bool:
    """
    Prevent open-redirects:
    only allow redirects to your own host.
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ("http", "https")) and (ref_url.netloc == test_url.netloc)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login (UUID-safe, secure next redirect)"""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()

    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=bool(getattr(form, "remember_me", None) and form.remember_me.data))

            next_page = request.args.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            return redirect(url_for("dashboard.index"))

        flash("Invalid email or password", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration (prevents duplicate email/username, UUID-ready)"""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        username = (form.username.data or "").strip()
        email = (form.email.data or "").strip().lower()

        # Prevent duplicates (friendly errors)
        if User.query.filter_by(email=email).first():
            flash("That email is already registered. Please log in instead.", "warning")
            return render_template("auth/register.html", form=form)

        if User.query.filter_by(username=username).first():
            flash("That username is already taken. Please choose another.", "warning")
            return render_template("auth/register.html", form=form)

        role = (form.role.data or "student").strip().lower()
        if role not in {"student", "instructor", "admin"}:
            role = "student"

        user = User(
            username=username,
            email=email,
            first_name=(form.first_name.data or "").strip(),
            last_name=(form.last_name.data or "").strip(),
            role=role,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout"""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))