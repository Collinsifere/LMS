from datetime import datetime
import os
import csv
from io import StringIO
from flask import request 
from flask import (
    Blueprint,
    render_template,
    current_app,
    redirect,
    url_for,
    flash,
    Response,
)
from flask_login import login_required, current_user
from sqlalchemy.orm import selectinload

from models import db, Assignment, Submission, Course, Enrollment
from forms import AssignmentForm, SubmissionForm, GradingForm

# Shared helpers (single source of truth)
# NOTE: If utils.py is not at project root, adjust import (e.g. from app.utils import ...)
from utils import allowed_file, sanitize_filename


assignments_bp = Blueprint("assignments", __name__)


# =========================================================
# Access Helpers
# =========================================================

def _require_instructor_or_admin(course: Course) -> bool:
    return (current_user.role == "admin") or (course.instructor_id == current_user.id)


def _user_can_access_course(course: Course) -> bool:
    if _require_instructor_or_admin(course):
        return True

    return (
        Enrollment.query
        .filter_by(user_id=current_user.id, course_id=course.id, status="active")
        .first()
        is not None
    )


# =========================================================
# Create Assignment
# =========================================================

@assignments_bp.route("/course/<uuid:course_id>/create", methods=["GET", "POST"])
@login_required
def create(course_id):
    """Create a new assignment (UUID-safe + ViewModel template support)"""
    course = Course.query.get_or_404(course_id)

    if not _require_instructor_or_admin(course):
        flash("You can only create assignments for your own courses.", "danger")
        return redirect(url_for("courses.view", course_id=course.id))

    form = AssignmentForm()

    if form.validate_on_submit():
        assignment = Assignment(
            course_id=course.id,
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            max_score=form.max_score.data,
        )
        db.session.add(assignment)
        db.session.commit()

        flash("Assignment created successfully!", "success")
        return redirect(url_for("courses.view", course_id=course.id))

    # -----------------------------------------
    # ViewModel for template (logic-free)
    # -----------------------------------------
    course_view = {
        "id": str(course.id),
        "title": course.title,
        "code": course.code,
        "course_url": url_for("courses.view", course_id=course.id),
        "dashboard_url": url_for("dashboard.index"),
    }

    return render_template(
        "assignments/create.html",
        form=form,
        course_view=course_view,
    )


# =========================================================
# View Assignment (Student + Instructor)
# =========================================================

@assignments_bp.route("/<uuid:assignment_id>")
@login_required
def view(assignment_id):
    """View assignment details (UUID-safe + logic-free templates + no N+1)"""
    assignment = (
        Assignment.query
        .options(selectinload(Assignment.course).selectinload(Course.instructor))
        .get_or_404(assignment_id)
    )
    course = assignment.course

    if not course:
        flash("Course not found for this assignment.", "danger")
        return redirect(url_for("courses.index"))

    if not _user_can_access_course(course):
        flash("You do not have access to this assignment.", "danger")
        return redirect(url_for("courses.index"))

    is_instructor = _require_instructor_or_admin(course)
    now = datetime.utcnow()

    # =====================================================
    # INSTRUCTOR VIEW (logic-free)
    # =====================================================
    if is_instructor:
        submissions = (
            Submission.query
            .options(selectinload(Submission.student))
            .filter_by(assignment_id=assignment.id)
            .order_by(Submission.submitted_at.desc())
            .all()
        )

        max_score = float(assignment.max_score or 0.0)

        assignment_view = {
            "id": str(assignment.id),
            "title": assignment.title,
            "description_text": assignment.description or "No description",
            "course_title": course.title,
            "course_url": url_for("courses.view", course_id=course.id),
            "dashboard_url": url_for("dashboard.index"),
            "due_display": (
                assignment.due_date.strftime("%B %d, %Y at %I:%M %p")
                if assignment.due_date else "No due date"
            ),
            "max_score_display": f"{max_score:g} points",
        }

        total = len(submissions)
        graded_scores = []
        graded_count = 0
        pending_count = 0

        submissions_view = []
        for s in submissions:
            student = s.student

            late_badge_html = ""
            if assignment.due_date and s.submitted_at and s.submitted_at > assignment.due_date:
                late_badge_html = '<span class="badge bg-warning text-dark">Late</span>'

            if s.score is not None:
                graded_count += 1
                graded_scores.append(float(s.score))
                status_badge_html = '<span class="badge bg-success">Graded</span>'
                score_line = f"{s.score} / {max_score:g}"
                percent_line = (
                    f"({(float(s.score) / max_score) * 100:.1f}%)"
                    if max_score > 0 else ""
                )
                action_label = "Review"
                action_icon = "bi bi-pencil"
                action_btn_class = "btn-outline-primary"
            else:
                pending_count += 1
                status_badge_html = '<span class="badge bg-warning text-dark">Pending</span>'
                score_line = ""
                percent_line = ""
                action_label = "Grade"
                action_icon = "bi bi-check-circle"
                action_btn_class = "btn-primary"

            submissions_view.append({
                "id": str(s.id),
                "student_name": (
                    f"{student.first_name or ''} {student.last_name or ''}".strip()
                    if student else "Student"
                ),
                "student_username": student.username if student else "",
                "student_email": student.email if student else "",
                "submitted_date": (
                    s.submitted_at.strftime("%b %d, %Y") if s.submitted_at else "N/A"
                ),
                "submitted_time": (
                    s.submitted_at.strftime("%I:%M %p") if s.submitted_at else ""
                ),
                "late_badge_html": late_badge_html,
                "status_badge_html": status_badge_html,
                "score_line": score_line,
                "percent_line": percent_line,
                "grade_url": url_for("assignments.grade", submission_id=s.id),
                "action_label": action_label,
                "action_icon": action_icon,
                "action_btn_class": action_btn_class,
            })

        avg_display = "-"
        avg_class = "text-muted"
        if graded_scores:
            avg = sum(graded_scores) / len(graded_scores)
            avg_display = f"{avg:.1f}"
            avg_class = "text-info"

        stats = {
            "has_submissions": total > 0,
            "total_submissions": total,
            "graded_count": graded_count,
            "pending_count": pending_count,
            "avg_score_display": avg_display,
            "avg_score_class": avg_class,
        }

        empty_state = {
            "title": "No submissions yet",
            "text": "Students haven't submitted any work for this assignment.",
        }

        export = {
            "csv_url": url_for("assignments.export_submissions_csv", assignment_id=assignment.id),
        }

        return render_template(
            "assignments/view_instructor.html",
            assignment_view=assignment_view,
            stats=stats,
            submissions_view=submissions_view,
            empty_state=empty_state,
            export=export,
        )

    # =====================================================
    # STUDENT VIEW (logic-free)
    # =====================================================

    submission = (
        Submission.query
        .filter_by(assignment_id=assignment.id, student_id=current_user.id)
        .first()
    )

    max_score = float(assignment.max_score or 0.0)

    due_display = "No due date"
    due_badge_html = ""
    if assignment.due_date:
        due_display = assignment.due_date.strftime("%B %d, %Y at %I:%M %p")
        if assignment.due_date < now:
            due_badge_html = ' <span class="badge bg-danger">Overdue</span>'
        else:
            due_badge_html = ' <span class="badge bg-success">Upcoming</span>'

    assignment_view = {
        "id": str(assignment.id),
        "title": assignment.title,
        "course_title": course.title,
        "course_url": url_for("courses.view", course_id=course.id),
        "description_text": assignment.description or "No description provided.",
        "due_display": due_display,
        "due_badge_html": due_badge_html,
        "max_score_display": f"{max_score:g} points",
    }

    submission_view = None
    status_badge_html = '<span class="badge bg-secondary">Not Submitted</span>'

    if submission:
        file_name = os.path.basename(submission.file_path) if submission.file_path else None
        is_graded = submission.score is not None

        if is_graded:
            status_badge_html = '<span class="badge bg-success">Graded</span>'
        else:
            status_badge_html = '<span class="badge bg-warning text-dark">Submitted</span>'

        submission_view = {
            "id": str(submission.id),
            "submitted_at_display": (
                submission.submitted_at.strftime("%B %d, %Y at %I:%M %p")
                if submission.submitted_at else "N/A"
            ),
            "content_text": submission.content or "",
            "file_name": file_name,
            "is_graded": is_graded,
            "score_display": (f"{submission.score} / {max_score:g}" if is_graded else ""),
            "percentage_display": (
                f"{(float(submission.score) / max_score) * 100:.1f}%"
                if is_graded and max_score > 0 else ""
            ),
            "graded_at_display": (
                submission.graded_at.strftime("%B %d, %Y at %I:%M %p")
                if submission.graded_at else ""
            ),
            "feedback_text": submission.feedback or "",
            "pending_text": "Your submission is pending grading.",
            "submit_url": url_for("assignments.submit", assignment_id=assignment.id),
            "submit_button_label": "Resubmit Assignment",
        }

    sidebar_view = {
        "status_badge_html": status_badge_html,
        "created_at_display": (
            assignment.created_at.strftime("%B %d, %Y")
            if assignment.created_at else "N/A"
        ),
        "instructor_name": (
            f"{course.instructor.first_name or ''} {course.instructor.last_name or ''}".strip()
            if course.instructor else "Instructor"
        ),
        "back_to_course_url": url_for("courses.view", course_id=course.id),
    }

    return render_template(
        "assignments/view.html",
        assignment_view=assignment_view,
        submission_view=submission_view,
        sidebar_view=sidebar_view,
        submit_url=url_for("assignments.submit", assignment_id=assignment.id),
        no_submission_title="You haven't submitted this assignment yet.",
        no_submission_text="Click the button below to submit your work.",
    )


# =========================================================
# Submit Assignment (ViewModel support)
# =========================================================

@assignments_bp.route("/<uuid:assignment_id>/submit", methods=["GET", "POST"])
@login_required
def submit(assignment_id):
    """Submit an assignment (UUID-safe + ViewModel template support)"""
    assignment = (
        Assignment.query
        .options(selectinload(Assignment.course).selectinload(Course.instructor))
        .get_or_404(assignment_id)
    )
    course = assignment.course

    if not course:
        flash("Course not found for this assignment.", "danger")
        return redirect(url_for("courses.index"))

    # Instructors/admins shouldn't submit
    if _require_instructor_or_admin(course):
        flash("Instructors cannot submit to their own assignments.", "warning")
        return redirect(url_for("assignments.view", assignment_id=assignment.id))

    # Must be enrolled (active)
    enrollment = (
        Enrollment.query
        .filter_by(user_id=current_user.id, course_id=course.id, status="active")
        .first()
    )
    if not enrollment:
        flash("You must be enrolled in the course to submit assignments.", "danger")
        return redirect(url_for("courses.index"))

    existing_submission = (
        Submission.query
        .filter_by(assignment_id=assignment.id, student_id=current_user.id)
        .first()
    )

    form = SubmissionForm()

    # -----------------------------
    # Handle POST
    # -----------------------------
    if form.validate_on_submit():
        file_path = None

        # File upload (optional)
        if getattr(form, "file", None) and form.file.data:
            file = form.file.data

            if not allowed_file(file.filename):
                flash("File type not allowed. Upload: pdf, doc, docx, txt, zip.", "danger")
                return redirect(url_for("assignments.submit", assignment_id=assignment.id))

            safe_name = sanitize_filename(file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            final_name = f"{current_user.id}_{timestamp}_{safe_name}"

            upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, final_name)
            file.save(file_path)

        if existing_submission:
            existing_submission.content = form.content.data
            if file_path:
                existing_submission.file_path = file_path
            existing_submission.submitted_at = datetime.utcnow()
            message = "Assignment resubmitted successfully!"
        else:
            submission = Submission(
                assignment_id=assignment.id,
                student_id=current_user.id,
                content=form.content.data,
                file_path=file_path,
            )
            db.session.add(submission)
            message = "Assignment submitted successfully!"

        db.session.commit()
        flash(message, "success")
        return redirect(url_for("assignments.view", assignment_id=assignment.id))

    # -----------------------------
    # ViewModels for template
    # -----------------------------
    is_resubmission = existing_submission is not None
    now = datetime.utcnow()

    due_display = "No due date"
    due_badge_html = ""
    if assignment.due_date:
        due_display = assignment.due_date.strftime("%B %d, %Y at %I:%M %p")
        if assignment.due_date < now:
            due_badge_html = '<span class="badge bg-danger ms-2">Overdue</span>'

    max_score = float(assignment.max_score or 0.0)

    assignment_view = {
        "title": assignment.title,
        "course_title": course.title,
        "description_text": assignment.description or "",
        "due_display": due_display,
        "due_badge_html": due_badge_html,
        "max_score_display": f"{max_score:g} points",
    }

    previous_submission = {
        "warning": is_resubmission,
        "show_previous_card": is_resubmission,
        "submitted_at_display": (
            f"You previously submitted on {existing_submission.submitted_at.strftime('%B %d, %Y at %I:%M %p')}."
            if is_resubmission and existing_submission.submitted_at
            else ""
        ),
        "file_name": (
            os.path.basename(existing_submission.file_path)
            if is_resubmission and existing_submission.file_path
            else None
        ),
        "content_text": existing_submission.content if is_resubmission else "",
        "is_graded": (existing_submission.score is not None) if is_resubmission else False,
        "score_display": (
            f"{existing_submission.score} / {max_score:g}"
            if is_resubmission and existing_submission.score is not None
            else ""
        ),
        "percentage_display": (
            f"({(float(existing_submission.score) / max_score) * 100:.1f}%)"
            if is_resubmission and existing_submission.score is not None and max_score > 0
            else ""
        ),
        "feedback_text": (existing_submission.feedback or "") if is_resubmission else "",
    }

    nav = {
        "dashboard_url": url_for("dashboard.index"),
        "course_url": url_for("courses.view", course_id=course.id),
        "assignment_url": url_for("assignments.view", assignment_id=assignment.id),
        "course_title": course.title,
        "assignment_title": assignment.title,
    }

    return render_template(
        "assignments/submit.html",
        form=form,
        page_title="Resubmit Assignment" if is_resubmission else "Submit Assignment",
        header_title="Resubmit Assignment" if is_resubmission else "Submit Assignment",
        submit_button_label="Resubmit Assignment" if is_resubmission else "Submit Assignment",
        nav=nav,
        assignment_view=assignment_view,
        previous_submission=previous_submission,
    )


# =========================================================
# Grade Submission
# =========================================================

@assignments_bp.route("/submission/<uuid:submission_id>/grade", methods=["GET", "POST"])
@login_required
def grade(submission_id):
    """Grade a submission (UUID-safe + ViewModel + no N+1)"""
    submission = (
        Submission.query
        .options(
            selectinload(Submission.assignment).selectinload(Assignment.course).selectinload(Course.instructor),
            selectinload(Submission.student),
        )
        .get_or_404(submission_id)
    )

    assignment = submission.assignment
    course = assignment.course if assignment else None

    if not assignment or not course:
        flash("Assignment/course not found for this submission.", "danger")
        return redirect(url_for("dashboard.index"))

    if not _require_instructor_or_admin(course):
        flash("Only the course instructor can grade assignments.", "danger")
        return redirect(url_for("dashboard.index"))

    form = GradingForm()

    # Pre-populate form (edit/review existing grade)
    if submission.score is not None and request.method == "GET":
        form.score.data = submission.score
    if submission.feedback and request.method == "GET":
        form.feedback.data = submission.feedback

    if form.validate_on_submit():
        submission.score = form.score.data
        submission.feedback = form.feedback.data
        submission.graded_at = datetime.utcnow()
        db.session.commit()

        flash("Submission graded successfully!", "success")
        return redirect(url_for("assignments.view", assignment_id=assignment.id))

    max_score_val = float(assignment.max_score or 0.0)

    assignment_view = {
        "title": assignment.title,
        "course_title": course.title,
        "max_score_value": max_score_val,
        "max_score_display": f"{max_score_val:g} points",
    }

    student = submission.student
    student_view = {
        "name": (
            f"{student.first_name or ''} {student.last_name or ''}".strip()
            if student else "Student"
        ),
        "email": student.email if student else "",
        "username": student.username if student else "",
    }

    submitted_at_display = (
        submission.submitted_at.strftime("%B %d, %Y at %I:%M %p")
        if submission.submitted_at else "N/A"
    )

    submission_view = {
        "submitted_at_display": submitted_at_display,
        "content_text": submission.content or "",
        "file_name": os.path.basename(submission.file_path) if submission.file_path else None,
        "file_path": submission.file_path or None,
    }

    # Late logic (optional)
    late_view = None
    if assignment.due_date and submission.submitted_at and submission.submitted_at > assignment.due_date:
        hours_late = (submission.submitted_at - assignment.due_date).total_seconds() / 3600.0
        late_view = {
            "is_late": True,
            "late_text": f"Submitted {hours_late:.1f} hours after the deadline.",
        }

    nav = {
        "dashboard_url": url_for("dashboard.index"),
        "course_url": url_for("courses.view", course_id=course.id),
        "assignment_url": url_for("assignments.view", assignment_id=assignment.id),
    }

    feedback_templates = [
        {"label": "✓ Excellent work", "text": "Excellent work! You demonstrated a thorough understanding of the topic."},
        {"label": "✓ Good effort, needs improvement", "text": "Good effort! Consider reviewing the following areas: "},
        {"label": "✓ Request meeting", "text": "Please see me during office hours to discuss this assignment."},
        {"label": "✓ Late submission", "text": "Late submission noted. "},
    ]

    current_grade = None
    if submission.score is not None:
        pct = ""
        if max_score_val > 0:
            pct = f" ({(float(submission.score) / max_score_val) * 100:.1f}%)"
        current_grade = {
            "is_graded": True,
            "score_display": f"{submission.score} / {max_score_val:g}{pct}",
            "graded_at_display": (
                submission.graded_at.strftime("%B %d, %Y at %I:%M %p")
                if submission.graded_at else ""
            ),
        }

    return render_template(
        "assignments/grade.html",
        page_title="Grade Submission",
        nav=nav,
        assignment_view=assignment_view,
        student_view=student_view,
        submission_view=submission_view,
        late_view=late_view,
        feedback_templates=feedback_templates,
        current_grade=current_grade,
        form=form,
    )


# =========================================================
# Export CSV (Instructor Only)
# =========================================================

@assignments_bp.route("/<uuid:assignment_id>/export/submissions.csv")
@login_required
def export_submissions_csv(assignment_id):
    """Export submissions to CSV (server-side, no JS scraping)"""
    assignment = (
        Assignment.query
        .options(selectinload(Assignment.course))
        .get_or_404(assignment_id)
    )

    course = assignment.course
    if not course:
        flash("Course not found for this assignment.", "danger")
        return redirect(url_for("dashboard.index"))

    if not _require_instructor_or_admin(course):
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))

    submissions = (
        Submission.query
        .options(selectinload(Submission.student))
        .filter_by(assignment_id=assignment.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student Name", "Email", "Username",
        "Submitted At", "Status",
        "Score", "Percentage", "Feedback"
    ])

    max_score = float(assignment.max_score or 0.0)

    for s in submissions:
        student = s.student
        name = (
            f"{student.first_name or ''} {student.last_name or ''}".strip()
            if student else ""
        )
        email = student.email if student else ""
        username = student.username if student else ""
        submitted_at = s.submitted_at.isoformat() if s.submitted_at else ""
        status = "Graded" if s.score is not None else "Pending"

        score = ""
        percentage = ""
        if s.score is not None:
            score = str(s.score)
            if max_score > 0:
                percentage = f"{(float(s.score) / max_score) * 100:.1f}%"

        writer.writerow([
            name, email, username,
            submitted_at, status,
            score, percentage,
            s.feedback or ""
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                f'attachment; filename="assignment_submissions_{assignment.id}.csv"'
        },
    )