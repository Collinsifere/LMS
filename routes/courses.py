from functools import wraps
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from models import db, Course, Lesson, Enrollment
from forms import CourseForm, LessonForm
courses_bp = Blueprint("courses", __name__)


def instructor_required(f):
    """Decorator to require instructor or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ["instructor", "admin"]:
            flash("You need instructor privileges to access this page.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated_function


def _youtube_embed_url(raw_url: str) -> str | None:
    """Return a YouTube embed URL if possible, else None."""
    if not raw_url:
        return None

    try:
        u = raw_url.strip()
        parsed = urlparse(u)
        host = (parsed.netloc or "").lower()
        path = parsed.path or ""

        video_id = None

        # youtube.com/watch?v=...
        if "youtube.com" in host:
            qs = parse_qs(parsed.query or "")
            if "v" in qs and qs["v"]:
                video_id = qs["v"][0]

        # youtu.be/<id>
        if "youtu.be" in host and path:
            video_id = path.strip("/").split("/")[0]

        if not video_id:
            return None

        return f"https://www.youtube.com/embed/{video_id}"
    except Exception:
        return None


@courses_bp.route("/")
@login_required
def index():
    """List all available courses (optimized)"""
    if current_user.role in ["instructor", "admin"]:
        # Courses taught by instructor/admin (admin logic can be expanded later)
        courses = (
            Course.query
            .options(selectinload(Course.instructor))
            .filter(Course.instructor_id == current_user.id)
            .order_by(Course.created_at.desc())
            .all()
        )

        course_ids = [c.id for c in courses]

        # Enrollment counts per course (fast aggregate)
        enrollment_counts = {}
        if course_ids:
            enrollment_counts = dict(
                db.session.query(
                    Enrollment.course_id,
                    func.count(Enrollment.id),
                )
                .filter(
                    Enrollment.course_id.in_(course_ids),
                    Enrollment.status == "active",
                )
                .group_by(Enrollment.course_id)
                .all()
            )

        # View model (optional)
        courses_view = [{"course": c, "students": int(enrollment_counts.get(c.id, 0))} for c in courses]

        # Keep your original "courses" for backward compatibility with your current template.
        return render_template("courses/index.html", courses=courses, courses_view=courses_view)

    # Students only see published courses
    courses = (
        Course.query
        .options(selectinload(Course.instructor))
        .filter(Course.is_published.is_(True))
        .order_by(Course.created_at.desc())
        .all()
    )
    return render_template("courses/index.html", courses=courses)


@courses_bp.route("/<uuid:course_id>")
@login_required
def view(course_id):
    """
    View course details (UUID-safe + optimized + NO N+1 for the current view.html)
    Also precomputes logic-free variables if you switch to the refactored template.
    """
    course = (
        Course.query
        .options(
            selectinload(Course.instructor),
            selectinload(Course.lessons),
            selectinload(Course.assignments),
            selectinload(Course.enrollments).selectinload(Enrollment.user),
        )
        .get_or_404(course_id)
    )

    # Enrollment check (single query)
    enrollment = (
        Enrollment.query
        .filter_by(user_id=current_user.id, course_id=course.id)
        .first()
    )

    is_instructor = (course.instructor_id == current_user.id) or (current_user.role == "admin")

    if not enrollment and not is_instructor and not course.is_published:
        flash("You do not have access to this course.", "danger")
        return redirect(url_for("courses.index"))

    now = datetime.utcnow()

    # ---------------------------------------------------------
    # Keep backward compatibility: your current view.html expects:
    # course, lessons, enrollment, is_instructor, now
    # ---------------------------------------------------------
    lessons = sorted(course.lessons, key=lambda l: (l.order or 0, l.created_at or now))

    # ---------------------------------------------------------
    # OPTIONAL (logic-free template support) — safe to pass now
    # If you keep your current template, it can ignore these.
    # ---------------------------------------------------------
    instructor_name = "Instructor"
    if course.instructor:
        instructor_name = f"{course.instructor.first_name or ''} {course.instructor.last_name or ''}".strip() or "Instructor"

    lessons_sorted = lessons
    assignments_sorted = sorted(course.assignments, key=lambda a: (a.due_date is None, a.due_date or now, a.created_at or now))

    lessons_view = []
    for idx, lesson in enumerate(lessons_sorted, start=1):
        duration_display = f"{int(lesson.duration_minutes)} minutes" if lesson.duration_minutes else ""
        content_preview = ""
        if lesson.content:
            content_preview = (lesson.content[:100] + "...") if len(lesson.content) > 100 else lesson.content

        embed_url = _youtube_embed_url(lesson.video_url or "")
        lessons_view.append({
            "index": idx,
            "id": str(lesson.id),
            "title": lesson.title,
            "duration_display": duration_display,
            "has_duration": bool(duration_display),
            "has_content": bool(lesson.content),
            "content_preview": content_preview,
            "content_full": lesson.content or "",
            "has_video": bool(lesson.video_url),
            "is_youtube": bool(embed_url),
            "video_embed_url": embed_url or "",
            "video_raw_url": lesson.video_url or "",
            "collapse_id": f"lesson{lesson.id}",
        })

    assignments_view = []
    for a in assignments_sorted:
        due_display = "No due date"
        badge_html = ""
        if a.due_date:
            due_display = f"Due: {a.due_date.strftime('%B %d, %Y at %I:%M %p')}"
            badge_html = (
                '<span class="badge bg-danger mt-1">Overdue</span>'
                if a.due_date < now
                else '<span class="badge bg-success mt-1">Upcoming</span>'
            )

        assignments_view.append({
            "url": url_for("assignments.view", assignment_id=a.id),
            "title": a.title,
            "due_display": due_display,
            "points_display": f"{a.max_score} pts",
            "badge_html": badge_html,
        })

    enrollments_sorted = sorted(course.enrollments, key=lambda e: (e.enrolled_at or now), reverse=True)
    preview = enrollments_sorted[:5]
    extra_count = max(0, len(enrollments_sorted) - 5)

    students_preview_view = []
    for e in preview:
        u = e.user
        full_name = "Student"
        email = ""
        if u:
            full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or (u.username or "Student")
            email = u.email or ""
        students_preview_view.append({
            "full_name": full_name,
            "email": email,
            "progress_display": f"{round(float(e.progress or 0.0), 0)}%",
        })

    show_enroll_section = (not is_instructor) and (enrollment is None)
    show_progress_section = (not is_instructor) and (enrollment is not None)

    progress_value = float(enrollment.progress or 0.0) if enrollment else 0.0
    progress_display = f"{round(progress_value, 1)}%" if enrollment else "0%"

    return render_template(
        "courses/view.html",

        # current template compatibility
        course=course,
        lessons=lessons,
        enrollment=enrollment,
        is_instructor=is_instructor,
        now=now,

        # logic-free extras (optional)
        course_title=course.title,
        course_code=course.code or "",
        course_description=course.description or "No description available.",
        instructor_name=instructor_name,
        lessons_count=len(lessons_sorted),
        assignments_count=len(assignments_sorted),
        students_count=len(course.enrollments),
        published_text="Published" if course.is_published else "Draft",
        published_icon_class="text-success" if course.is_published else "text-warning",

        show_enroll_section=show_enroll_section,
        show_progress_section=show_progress_section,
        course_is_published=bool(course.is_published),
        progress_value=progress_value,
        progress_display=progress_display,

        lessons_view=lessons_view,
        has_lessons=bool(lessons_view),
        assignments_view=assignments_view,
        has_assignments=bool(assignments_view),

        dashboard_url=url_for("dashboard.index"),
        courses_index_url=url_for("courses.index"),
        edit_course_url=url_for("courses.edit", course_id=course.id),
        create_lesson_url=url_for("courses.create_lesson", course_id=course.id),
        create_assignment_url=url_for("assignments.create", course_id=course.id),
        enroll_action_url=url_for("courses.enroll", course_id=course.id),

        show_students_panel=bool(is_instructor),
        students_preview_view=students_preview_view,
        students_more_text=(f"and {extra_count} more..." if extra_count > 0 else ""),
    )


@courses_bp.route("/create", methods=["GET", "POST"])
@login_required
@instructor_required
def create():
    """Create a new course"""
    form = CourseForm()

    if form.validate_on_submit():
        course = Course(
            title=form.title.data,
            description=form.description.data,
            code=form.code.data,
            instructor_id=current_user.id,
            is_published=form.is_published.data,
        )

        db.session.add(course)
        db.session.commit()

        flash("Course created successfully!", "success")
        return redirect(url_for("courses.view", course_id=course.id))

    return render_template("courses/create.html", form=form)


@courses_bp.route("/<uuid:course_id>/edit", methods=["GET", "POST"])
@login_required
@instructor_required
def edit(course_id):
    """Edit course (UUID-safe)"""
    course = Course.query.get_or_404(course_id)

    # Admin can edit any course; instructor can edit own
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        flash("You can only edit your own courses.", "danger")
        return redirect(url_for("courses.index"))

    form = CourseForm(obj=course)

    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.code = form.code.data
        course.is_published = form.is_published.data

        db.session.commit()
        flash("Course updated successfully!", "success")
        return redirect(url_for("courses.view", course_id=course.id))

    return render_template("courses/edit.html", form=form, course=course)


@courses_bp.route("/<uuid:course_id>/enroll", methods=["POST"])
@login_required
def enroll(course_id):
    """Enroll in a course (UUID-safe)"""
    course = Course.query.get_or_404(course_id)

    if not course.is_published:
        flash("This course is not available for enrollment.", "danger")
        return redirect(url_for("courses.index"))

    existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if existing:
        flash("You are already enrolled in this course.", "info")
        return redirect(url_for("courses.view", course_id=course.id))

    enrollment = Enrollment(user_id=current_user.id, course_id=course.id, status="active")
    db.session.add(enrollment)
    db.session.commit()

    flash("Successfully enrolled in the course!", "success")
    return redirect(url_for("courses.view", course_id=course.id))


@courses_bp.route("/<uuid:course_id>/lessons/create", methods=["GET", "POST"])
@login_required
@instructor_required
def create_lesson(course_id):
    """Create a new lesson for a course (UUID-safe)"""
    course = Course.query.get_or_404(course_id)

    if current_user.role != "admin" and course.instructor_id != current_user.id:
        flash("You can only add lessons to your own courses.", "danger")
        return redirect(url_for("courses.index"))

    form = LessonForm()

    if form.validate_on_submit():
        lesson = Lesson(
            course_id=course.id,
            title=form.title.data,
            content=form.content.data,
            video_url=form.video_url.data,
            duration_minutes=form.duration_minutes.data,
            order=form.order.data,
        )

        db.session.add(lesson)
        db.session.commit()

        flash("Lesson created successfully!", "success")
        return redirect(url_for("courses.view", course_id=course.id))

    return render_template("courses/create_lesson.html", form=form, course=course)