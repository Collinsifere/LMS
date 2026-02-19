import os
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def calculate_progress(enrollment):
    """Calculate course progress for a student"""
    # This is a simple example - you can make it more sophisticated
    # by tracking completed lessons, assignments, etc.
    course = enrollment.course
    total_lessons = len(course.lessons)
    
    if total_lessons == 0:
        return 0.0
    
    # For now, just return the stored progress
    # You could calculate this based on completed lessons/assignments
    return enrollment.progress


def is_assignment_overdue(assignment):
    """Check if an assignment is past its due date"""
    from datetime import datetime
    if assignment.due_date:
        return datetime.utcnow() > assignment.due_date
    return False


def format_date(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime('%B %d, %Y at %I:%M %p')
    return 'N/A'


def allowed_file(filename, allowed_extensions=None):
    """Check if a file has an allowed extension"""
    if allowed_extensions is None:
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'zip'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_size(file_path):
    """Get file size in human readable format"""
    if not os.path.exists(file_path):
        return 'N/A'
    
    size_bytes = os.path.getsize(file_path)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"


def paginate_query(query, page, per_page=20):
    """Paginate a SQLAlchemy query"""
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    return pagination


def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    from werkzeug.utils import secure_filename
    return secure_filename(filename)
