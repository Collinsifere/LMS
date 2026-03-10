from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import expression

from models import (
    db,
    User,
    Course,
    Lesson,
    Enrollment,
    Assignment,
    Submission,
    # Agentic AI models:
    LearningAnalytics,
    KnowledgeGap,
    CourseTopic,
    StudentActivity,
    InterventionLog,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """Main dashboard - routes to appropriate dashboard based on role"""
    if current_user.role == "instructor":
        return redirect(url_for("dashboard.instructor"))
    return redirect(url_for("dashboard.student"))


@dashboard_bp.route("/student")
@login_required
def student():
    """Student dashboard (Agentic AI enabled, optimized, logic-free template support)"""

    student_id = current_user.id

    # ---------------------------------------
    # Enrollments (active) - eager load course + instructor (NO N+1)
    # ---------------------------------------
    enrollments = (
        Enrollment.query
        .options(selectinload(Enrollment.course).selectinload(Course.instructor))
        .filter(Enrollment.user_id == student_id, Enrollment.status == "active")
        .all()
    )
    enrolled_course_ids = [e.course_id for e in enrollments]

    # ---------------------------------------
    # Dashboard counts + avg progress (computed in SQL, not Python)
    # NOTE: completed_courses_count is computed across ALL enrollments for the user
    # ---------------------------------------
    enrolled_courses_count = len(enrollments)

    completed_courses_count = (
        db.session.query(func.count(Enrollment.id))
        .filter(Enrollment.user_id == student_id, Enrollment.status == "completed")
        .scalar()
    ) or 0

    avg_progress = (
        db.session.query(func.coalesce(func.avg(Enrollment.progress), 0.0))
        .filter(Enrollment.user_id == student_id, Enrollment.status == "active")
        .scalar()
    ) or 0.0
    avg_progress_display = f"{round(float(avg_progress), 1)}%"

    # ---------------------------------------
    # Upcoming assignments (limit) - eager load course (NO N+1)
    # Order NULL due dates last
    # ---------------------------------------
    upcoming_assignments = []
    if enrolled_course_ids:
        upcoming_assignments = (
            Assignment.query
            .options(selectinload(Assignment.course))
            .filter(Assignment.course_id.in_(enrolled_course_ids))
            .order_by(
                expression.case((Assignment.due_date.is_(None), 1), else_=0).asc(),
                Assignment.due_date.asc(),
            )
            .limit(5)
            .all()
        )

    has_upcoming_assignments = len(upcoming_assignments) > 0
    upcoming_assignments_count = len(upcoming_assignments)

    now = datetime.utcnow()
    upcoming_assignments_view = []
    for a in upcoming_assignments:
        course_title = a.course.title if a.course else "Course"

        if not a.due_date:
            due_display = "No due date"
            badge_text = "Open"
        else:
            due_display = f"Due {a.due_date.strftime('%b %d, %I:%M %p')}"
            days_left = (a.due_date - now).total_seconds() / 86400.0
            if days_left < 0:
                badge_text = "Overdue"
            elif days_left <= 2:
                badge_text = "Urgent"
            else:
                badge_text = "Due Soon"

        upcoming_assignments_view.append({
            "url": url_for("assignments.view", assignment_id=a.id),
            "title": a.title,
            "course_title": course_title,
            "due_display": due_display,
            "badge_text": badge_text,
        })

    # ---------------------------------------
    # AI Analytics (latest snapshot)
    # ---------------------------------------
    analytics = (
        LearningAnalytics.query
        .filter(LearningAnalytics.student_id == student_id)
        .order_by(LearningAnalytics.created_at.desc())
        .first()
    )

    dropout_risk_display = "N/A"
    recommended_action_text = "Complete your next assignment and review the latest lesson."

    if analytics:
        if analytics.dropout_risk is not None:
            dropout_risk_display = f"{round(float(analytics.dropout_risk) * 100, 0)}%"
        if analytics.recommended_action:
            recommended_action_text = analytics.recommended_action

    # ---------------------------------------
    # Knowledge gaps (top 5 weakest topics)
    # ---------------------------------------
    knowledge_gaps = (
        db.session.query(
            KnowledgeGap,
            CourseTopic.topic_name,
            CourseTopic.course_id,
        )
        .join(CourseTopic, KnowledgeGap.topic_id == CourseTopic.id)
        .filter(KnowledgeGap.student_id == student_id)
        .order_by(KnowledgeGap.mastery_level.asc())
        .limit(5)
        .all()
    )

    has_knowledge_gaps = len(knowledge_gaps) > 0
    no_gaps_text = "No knowledge gaps detected yet."

    knowledge_gaps_view = []
    for kg, topic_name, _course_id in knowledge_gaps:
        mastery_pct = round(float(kg.mastery_level or 0.0) * 100.0, 0)
        knowledge_gaps_view.append({
            "topic_name": topic_name,
            "mastery_display": f"Mastery: {mastery_pct}%",
            "recommendation_text": "Recommended: review lesson materials and attempt practice questions.",
        })

    # ---------------------------------------
    # Activity summary (last 7 days)
    # ---------------------------------------
    since = datetime.utcnow() - timedelta(days=7)

    total_minutes_last_7_days = (
        db.session.query(func.coalesce(func.sum(StudentActivity.time_spent_minutes), 0))
        .filter(
            StudentActivity.student_id == student_id,
            StudentActivity.created_at >= since,
        )
        .scalar()
    ) or 0
    total_minutes_last_7_days = int(total_minutes_last_7_days)

    last_activity = (
        StudentActivity.query
        .filter(StudentActivity.student_id == student_id)
        .order_by(StudentActivity.created_at.desc())
        .first()
    )

    last_activity_short = "N/A"
    last_activity_text = "Last activity: Not recorded yet"
    if last_activity:
        last_activity_short = last_activity.activity_type or "Activity"
        last_activity_text = f"Last activity: {last_activity_short}"

    study_time_display = f"{total_minutes_last_7_days} mins"

    # ---------------------------------------
    # Intervention status (simple trigger)
    # ---------------------------------------
    intervention_needed = False

    if analytics and analytics.dropout_risk is not None and float(analytics.dropout_risk) >= 0.60:
        intervention_needed = True

    if last_activity and last_activity.created_at < (datetime.utcnow() - timedelta(days=5)):
        intervention_needed = True

    latest_intervention = (
        InterventionLog.query
        .filter(InterventionLog.student_id == student_id)
        .order_by(InterventionLog.triggered_at.desc())
        .first()
    )

    latest_intervention_text = ""
    if latest_intervention:
        itype = latest_intervention.intervention_type or "Intervention"
        risk = latest_intervention.risk_level or "risk"
        latest_intervention_text = f"Last intervention: {itype} ({risk})"

    intervention_cta_url = url_for("courses.index")
    intervention_cta_label = "Find practice materials"

    # ---------------------------------------
    # Course overview (logic-free objects)
    # - Uses enrollments already loaded with course+instructor (NO N+1)
    # - Adds avg_score via one aggregate query
    # ---------------------------------------
    has_courses = enrolled_courses_count > 0
    empty_courses_title = "No Enrolled Courses"
    empty_courses_text = "Start your learning journey by enrolling in a course!"

    course_overview = []
    if enrolled_course_ids:
        avg_scores_by_course = dict(
            db.session.query(
                Assignment.course_id,
                func.avg(Submission.score),
            )
            .join(Submission, Submission.assignment_id == Assignment.id)
            .filter(
                Submission.student_id == student_id,
                Assignment.course_id.in_(enrolled_course_ids),
                Submission.score.isnot(None),
            )
            .group_by(Assignment.course_id)
            .all()
        )

        for e in enrollments:
            c = e.course
            if not c:
                continue

            instructor_name = "Instructor"
            if c.instructor:
                instructor_name = f"{(c.instructor.first_name or '').strip()} {(c.instructor.last_name or '').strip()}".strip() or "Instructor"

            progress_value = round(float(e.progress or 0.0), 1)
            progress_display = f"{progress_value}%"

            avg_score = avg_scores_by_course.get(e.course_id)
            avg_score_display = "Avg score: N/A"
            if avg_score is not None:
                avg_score_display = f"Avg score: {round(float(avg_score), 1)}"

            status_badge = ""
            if e.status == "completed":
                status_badge = '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Completed</span>'

            course_overview.append({
                "course_code": c.code or "",
                "course_title": c.title,
                "instructor_name": instructor_name,
                "progress_value": progress_value,
                "progress_display": progress_display,
                "avg_score_display": avg_score_display,
                "status_badge": status_badge,
                "continue_url": url_for("courses.view", course_id=c.id),
            })

    # ---------------------------------------
    # Links + tips (logic-free)
    # ---------------------------------------
    browse_courses_url = url_for("courses.index")
    profile_url = "#"
    settings_url = "#"

    learning_tips = [
        "Set aside dedicated study time each day",
        "Complete assignments before the due date",
        "Review course materials regularly",
        "Ask questions early when stuck",
        "Take brief notes while studying",
    ]

    # ---------------------------------------
    # Render (logic-free template variables)
    # ---------------------------------------
    return render_template(
        "dashboard/student.html",

        # counts/stats
        enrolled_courses_count=enrolled_courses_count,
        upcoming_assignments_count=upcoming_assignments_count,
        completed_courses_count=int(completed_courses_count),
        avg_progress_display=avg_progress_display,

        # flags
        has_courses=has_courses,
        has_upcoming_assignments=has_upcoming_assignments,
        has_knowledge_gaps=has_knowledge_gaps,
        intervention_needed=intervention_needed,

        # AI snapshot
        dropout_risk_display=dropout_risk_display,
        recommended_action_text=recommended_action_text,
        last_activity_text=last_activity_text,

        # activity summary
        study_time_display=study_time_display,
        last_activity_short=last_activity_short,

        # intervention text + CTA
        latest_intervention_text=latest_intervention_text,
        intervention_cta_url=intervention_cta_url,
        intervention_cta_label=intervention_cta_label,

        # data views
        course_overview=course_overview,
        knowledge_gaps_view=knowledge_gaps_view,
        upcoming_assignments_view=upcoming_assignments_view,

        # empty states
        empty_courses_title=empty_courses_title,
        empty_courses_text=empty_courses_text,
        no_gaps_text=no_gaps_text,
        no_assignments_title="No pending assignments",
        no_assignments_text="You're all caught up!",

        # links/tips
        browse_courses_url=browse_courses_url,
        profile_url=profile_url,
        settings_url=settings_url,
        learning_tips=learning_tips,
    )
@dashboard_bp.route("/instructor")
@login_required
def instructor():
    """Instructor dashboard (optimized + logic-free template support)"""
    if current_user.role not in ["instructor", "admin"]:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.student"))

    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    course_ids = [c.id for c in courses]

    courses_count = len(courses)

    total_students = (
        Enrollment.query
        .join(Course, Enrollment.course_id == Course.id)
        .filter(
            Course.instructor_id == current_user.id,
            Enrollment.status == "active",
        )
        .count()
    )

    total_assignments = (
        Assignment.query
        .filter(Assignment.course_id.in_(course_ids))
        .count()
        if course_ids else 0
    )

    pending_submissions = []
    if course_ids:
        pending_submissions = (
            Submission.query
            .options(
                selectinload(Submission.assignment),
                selectinload(Submission.student),
            )
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .filter(
                Assignment.course_id.in_(course_ids),
                Submission.score.is_(None),
            )
            .order_by(Submission.submitted_at.desc())
            .limit(10)
            .all()
        )
    pending_count = len(pending_submissions)

    course_stats = []
    if course_ids:
        enrollment_counts = dict(
            db.session.query(Enrollment.course_id, func.count(Enrollment.id))
            .filter(Enrollment.course_id.in_(course_ids), Enrollment.status == "active")
            .group_by(Enrollment.course_id)
            .all()
        )

        lesson_counts = dict(
            db.session.query(Lesson.course_id, func.count(Lesson.id))
            .filter(Lesson.course_id.in_(course_ids))
            .group_by(Lesson.course_id)
            .all()
        )

        assignment_counts = dict(
            db.session.query(Assignment.course_id, func.count(Assignment.id))
            .filter(Assignment.course_id.in_(course_ids))
            .group_by(Assignment.course_id)
            .all()
        )

        avg_progress_by_course = dict(
            db.session.query(Enrollment.course_id, func.avg(Enrollment.progress))
            .filter(Enrollment.course_id.in_(course_ids), Enrollment.status == "active")
            .group_by(Enrollment.course_id)
            .all()
        )

        for c in courses:
            students = int(enrollment_counts.get(c.id, 0))
            lessons = int(lesson_counts.get(c.id, 0))
            assignments = int(assignment_counts.get(c.id, 0))

            avg_progress = avg_progress_by_course.get(c.id)
            avg_progress_display = "N/A" if avg_progress is None else f"{round(float(avg_progress), 1)}%"

            status_badge = (
                '<span class="badge bg-success">Live</span>'
                if c.is_published else
                '<span class="badge bg-secondary">Draft</span>'
            )

            course_stats.append({
                "course": c,
                "students": students,
                "lessons": lessons,
                "assignments": assignments,
                "avg_progress": avg_progress_display,
                "status_badge": status_badge,
            })

    return render_template(
        "dashboard/instructor.html",
        courses_count=courses_count,
        total_students=total_students,
        total_assignments=total_assignments,
        pending_count=pending_count,
        course_stats=course_stats,
        pending_submissions=pending_submissions,
    )