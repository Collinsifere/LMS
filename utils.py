import os
from datetime import datetime
from functools import wraps
from typing import Iterable, Optional, Set, Union

from flask import flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename


# -------------------------------------------------------------------
# Auth / Roles
# -------------------------------------------------------------------

def role_required(*roles: str):
    """
    Decorator: require the user to be authenticated and have one of the given roles.
    Usage:
        @role_required("instructor", "admin")
        def my_route(): ...
    """
    roles_set = set(roles)

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            if roles_set and current_user.role not in roles_set:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("dashboard.index"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# -------------------------------------------------------------------
# Dates / Display
# -------------------------------------------------------------------

def is_assignment_overdue(due_date: Optional[datetime]) -> bool:
    """
    Returns True if due_date exists and is in the past.
    Pass the datetime directly rather than the whole assignment object.
    """
    return bool(due_date and datetime.utcnow() > due_date)


def format_date(dt: Optional[datetime], fmt: str = "%B %d, %Y at %I:%M %p") -> str:
    """Format datetime for display."""
    return dt.strftime(fmt) if dt else "N/A"


# -------------------------------------------------------------------
# Files
# -------------------------------------------------------------------

DEFAULT_ALLOWED_EXTENSIONS: Set[str] = {"pdf", "doc", "docx", "txt", "zip"}


def allowed_file(filename: str, allowed_extensions: Optional[Iterable[str]] = None) -> bool:
    """
    Check if a file has an allowed extension.
    """
    if not filename or "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    allowed = set(allowed_extensions) if allowed_extensions is not None else DEFAULT_ALLOWED_EXTENSIONS
    return ext in allowed


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    return secure_filename(filename or "")


def get_file_size(file_path: str) -> str:
    """Get file size in human readable format."""
    if not file_path or not os.path.exists(file_path):
        return "N/A"

    size_bytes = float(os.path.getsize(file_path))

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"


# -------------------------------------------------------------------
# Pagination (Flask-SQLAlchemy compatible)
# -------------------------------------------------------------------

def paginate_query(query, page: Union[int, str], per_page: int = 20):
    """
    Paginate a SQLAlchemy query using Flask-SQLAlchemy's paginate helper.
    Safe when page comes from request.args (string).
    """
    try:
        page_int = int(page)
    except (TypeError, ValueError):
        page_int = 1

    if page_int < 1:
        page_int = 1

    if per_page < 1:
        per_page = 20

    return query.paginate(page=page_int, per_page=per_page, error_out=False)