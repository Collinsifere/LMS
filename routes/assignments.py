from flask import Blueprint, render_template, current_app, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Assignment, Submission, Course, Enrollment
from forms import AssignmentForm, SubmissionForm, GradingForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename

assignments_bp = Blueprint('assignments', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@assignments_bp.route('/course/<int:course_id>/create', methods=['GET', 'POST'])
@login_required
def create(course_id):
    """Create a new assignment"""
    course = Course.query.get_or_404(course_id)
    
    if course.instructor_id != current_user.id:
        flash('You can only create assignments for your own courses.', 'danger')
        return redirect(url_for('courses.view', course_id=course_id))
    
    form = AssignmentForm()
    
    if form.validate_on_submit():
        assignment = Assignment(
            course_id=course_id,
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            max_score=form.max_score.data
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('courses.view', course_id=course_id))
    
    return render_template('assignments/create.html', form=form, course=course)


@assignments_bp.route('/<int:assignment_id>')
@login_required
def view(assignment_id):
    """View assignment details"""
    assignment = Assignment.query.get_or_404(assignment_id)
    course = assignment.course
    
    # Check if user has access
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course.id
    ).first()
    
    is_instructor = course.instructor_id == current_user.id
    
    if not enrollment and not is_instructor:
        flash('You do not have access to this assignment.', 'danger')
        return redirect(url_for('courses.index'))
    
    # Get user's submission if it exists
    submission = None
    if not is_instructor:
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
    else:
        # For instructors, get all submissions
        submissions = Submission.query.filter_by(
            assignment_id=assignment_id
        ).all()
        return render_template('assignments/view_instructor.html',
                             assignment=assignment,
                             submissions=submissions)
    
    return render_template('assignments/view.html',
                         assignment=assignment,
                         submission=submission)


@assignments_bp.route('/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit(assignment_id):
    """Submit an assignment"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=assignment.course_id
    ).first()
    
    if not enrollment:
        flash('You must be enrolled in the course to submit assignments.', 'danger')
        return redirect(url_for('courses.index'))
    
    # Check if already submitted
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=current_user.id
    ).first()
    
    form = SubmissionForm()
    
    if form.validate_on_submit():
        file_path = None
        
        # Handle file upload
        if form.file.data:
            file = form.file.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{current_user.id}_{timestamp}_{filename}"
                
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
        
        if existing_submission:
            # Update existing submission
            existing_submission.content = form.content.data
            existing_submission.file_path = file_path or existing_submission.file_path
            existing_submission.submitted_at = datetime.utcnow()
            message = 'Assignment resubmitted successfully!'
        else:
            # Create new submission
            submission = Submission(
                assignment_id=assignment_id,
                student_id=current_user.id,
                content=form.content.data,
                file_path=file_path
            )
            db.session.add(submission)
            message = 'Assignment submitted successfully!'
        
        db.session.commit()
        flash(message, 'success')
        return redirect(url_for('assignments.view', assignment_id=assignment_id))
    
    return render_template('assignments/submit.html',
                         form=form,
                         assignment=assignment,
                         existing_submission=existing_submission)


@assignments_bp.route('/submission/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
def grade(submission_id):
    """Grade a submission"""
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment
    
    # Check if user is the course instructor
    if assignment.course.instructor_id != current_user.id:
        flash('Only the course instructor can grade assignments.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = GradingForm()
    
    if form.validate_on_submit():
        submission.score = form.score.data
        submission.feedback = form.feedback.data
        submission.graded_at = datetime.utcnow()
        
        db.session.commit()
        flash('Submission graded successfully!', 'success')
        return redirect(url_for('assignments.view', assignment_id=assignment.id))
    
    # Pre-populate form with existing values
    if submission.score:
        form.score.data = submission.score
        form.feedback.data = submission.feedback
    
    return render_template('assignments/grade.html',
                         form=form,
                         submission=submission,
                         assignment=assignment)
