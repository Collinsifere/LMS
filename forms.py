from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SelectField, IntegerField, FloatField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import User


class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')


class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('instructor', 'Instructor')
    ], default='student')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class CourseForm(FlaskForm):
    """Course creation/editing form"""
    title = StringField('Course Title', validators=[
        DataRequired(),
        Length(max=200)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    code = StringField('Course Code', validators=[
        DataRequired(),
        Length(max=20)
    ])
    is_published = BooleanField('Published')


class LessonForm(FlaskForm):
    """Lesson creation/editing form"""
    title = StringField('Lesson Title', validators=[
        DataRequired(),
        Length(max=200)
    ])
    content = TextAreaField('Content', validators=[Optional()])
    video_url = StringField('Video URL', validators=[Optional(), Length(max=500)])
    duration_minutes = IntegerField('Duration (minutes)', validators=[Optional()])
    order = IntegerField('Order', validators=[Optional()], default=0)


class AssignmentForm(FlaskForm):
    """Assignment creation/editing form"""
    title = StringField('Assignment Title', validators=[
        DataRequired(),
        Length(max=200)
    ])
    description = TextAreaField('Description', validators=[Optional()])
    due_date = DateTimeField('Due Date', validators=[Optional()], format='%Y-%m-%d %H:%M:%S')
    max_score = FloatField('Maximum Score', validators=[
        DataRequired(),
        NumberRange(min=0, message='Score must be positive')
    ], default=100.0)


class SubmissionForm(FlaskForm):
    """Assignment submission form"""
    content = TextAreaField('Submission Text', validators=[Optional()])
    file = FileField('Upload File', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'zip'], 'Only PDF, DOC, DOCX, TXT, and ZIP files allowed')
    ])


class GradingForm(FlaskForm):
    """Assignment grading form"""
    score = FloatField('Score', validators=[
        DataRequired(),
        NumberRange(min=0, message='Score must be positive')
    ])
    feedback = TextAreaField('Feedback', validators=[Optional()])
