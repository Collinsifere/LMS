from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from models import Course, Enrollment, Assignment, Submission

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard - routes to appropriate dashboard based on role"""
    if current_user.role == 'instructor':
        return redirect(url_for('dashboard.instructor'))
    else:
        return redirect(url_for('dashboard.student'))


@dashboard_bp.route('/student')
@login_required
def student():
    """Student dashboard"""
    # Get enrolled courses
    enrollments = Enrollment.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()

    # Get upcoming assignments
    enrolled_course_ids = [e.course_id for e in enrollments]
    upcoming_assignments = Assignment.query.filter(
        Assignment.course_id.in_(enrolled_course_ids)
    ).order_by(Assignment.due_date).limit(5).all()

    return render_template(
        'dashboard/student.html',
        enrollments=enrollments,
        upcoming_assignments=upcoming_assignments
    )


@dashboard_bp.route('/instructor')
@login_required
def instructor():
    """Instructor dashboard"""
    if current_user.role not in ['instructor', 'admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.student'))

    # Get courses taught by this instructor
    courses = Course.query.filter_by(instructor_id=current_user.id).all()

    # Get total student count (FIXED)
    total_students = (
        Enrollment.query
        .join(Course)
        .filter(Course.instructor_id == current_user.id)
        .filter(Enrollment.status == 'active')
        .count()
    )

    # Get recent submissions that need grading
    course_ids = [c.id for c in courses]
    pending_submissions = (
        Submission.query
        .join(Assignment)
        .filter(
            Assignment.course_id.in_(course_ids),
            Submission.score.is_(None)
        )
        .order_by(Submission.submitted_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        'dashboard/instructor.html',
        courses=courses,
        total_students=total_students,
        pending_submissions=pending_submissions
    )

