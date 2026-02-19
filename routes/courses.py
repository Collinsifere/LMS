from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Course, Lesson, Enrollment
from forms import CourseForm, LessonForm
from functools import wraps

courses_bp = Blueprint('courses', __name__)


def instructor_required(f):
    """Decorator to require instructor or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['instructor', 'admin']:
            flash('You need instructor privileges to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@courses_bp.route('/')
@login_required
def index():
    """List all available courses"""
    if current_user.role == 'instructor':
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    else:
        courses = Course.query.filter_by(is_published=True).all()
    
    return render_template('courses/index.html', courses=courses)


@courses_bp.route('/<int:course_id>')
@login_required
def view(course_id):
    """View course details"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled or is the instructor
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    is_instructor = course.instructor_id == current_user.id
    
    if not enrollment and not is_instructor and not course.is_published:
        flash('You do not have access to this course.', 'danger')
        return redirect(url_for('courses.index'))
    
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()
    
    return render_template('courses/view.html', 
                         course=course, 
                         lessons=lessons,
                         enrollment=enrollment,
                         is_instructor=is_instructor)


@courses_bp.route('/create', methods=['GET', 'POST'])
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
            is_published=form.is_published.data
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('courses.view', course_id=course.id))
    
    return render_template('courses/create.html', form=form)


@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit(course_id):
    """Edit course"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != current_user.id:
        flash('You can only edit your own courses.', 'danger')
        return redirect(url_for('courses.index'))
    
    form = CourseForm(obj=course)
    
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.code = form.code.data
        course.is_published = form.is_published.data
        
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('courses.view', course_id=course.id))
    
    return render_template('courses/edit.html', form=form, course=course)


@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    """Enroll in a course"""
    course = Course.query.get_or_404(course_id)
    
    if not course.is_published:
        flash('This course is not available for enrollment.', 'danger')
        return redirect(url_for('courses.index'))
    
    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing:
        flash('You are already enrolled in this course.', 'info')
    else:
        enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash('Successfully enrolled in the course!', 'success')
    
    return redirect(url_for('courses.view', course_id=course_id))


@courses_bp.route('/<int:course_id>/lessons/create', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_lesson(course_id):
    """Create a new lesson for a course"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != current_user.id:
        flash('You can only add lessons to your own courses.', 'danger')
        return redirect(url_for('courses.index'))
    
    form = LessonForm()
    
    if form.validate_on_submit():
        lesson = Lesson(
            course_id=course_id,
            title=form.title.data,
            content=form.content.data,
            video_url=form.video_url.data,
            duration_minutes=form.duration_minutes.data,
            order=form.order.data
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        flash('Lesson created successfully!', 'success')
        return redirect(url_for('courses.view', course_id=course_id))
    
    return render_template('courses/create_lesson.html', form=form, course=course)
