from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

# =====================================================
# USERS
# =====================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False, index=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    learning_style = db.Column(db.String(50))
    skill_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Flask-Login expects a string id
    def get_id(self):
        return str(self.id)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Relationships
    enrollments = db.relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    courses_taught = db.relationship("Course", back_populates="instructor")
    submissions = db.relationship("Submission", back_populates="student")
    activities = db.relationship("StudentActivity", back_populates="student")


# =====================================================
# COURSES
# =====================================================

class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(20), unique=True, index=True)

    instructor_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    instructor = db.relationship("User", back_populates="courses_taught")
    lessons = db.relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    topics = db.relationship("CourseTopic", back_populates="course", cascade="all, delete-orphan")

    activities = db.relationship("StudentActivity", back_populates="course", cascade="all, delete-orphan")
    interventions = db.relationship("InterventionLog", back_populates="course", cascade="all, delete-orphan")
    analytics = db.relationship("LearningAnalytics", back_populates="course", cascade="all, delete-orphan")


# =====================================================
# LESSONS
# =====================================================

class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=0, nullable=False)
    video_url = db.Column(db.String(500))
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    course = db.relationship("Course", back_populates="lessons")


# =====================================================
# ENROLLMENTS
# =====================================================

class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True)

    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    progress = db.Column(db.Float, default=0.0, nullable=False)  # 0–100
    status = db.Column(db.String(20), default="active", nullable=False, index=True)  # active/completed/dropped

    user = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
    )


# =====================================================
# ASSIGNMENTS
# =====================================================

class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Float, default=100.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    generated_by_ai = db.Column(db.Boolean, default=False, nullable=False)

    course = db.relationship("Course", back_populates="assignments")
    submissions = db.relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


# =====================================================
# SUBMISSIONS
# =====================================================

class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    assignment_id = db.Column(UUID(as_uuid=True), db.ForeignKey("assignments.id"), nullable=False, index=True)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)

    content = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    graded_at = db.Column(db.DateTime)

    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship("User", back_populates="submissions")

    plagiarism_reports = db.relationship("PlagiarismReport", back_populates="submission", cascade="all, delete-orphan")
    integrity_scores = db.relationship("IntegrityScore", back_populates="submission", cascade="all, delete-orphan")


# =====================================================
# CONTENT GENERATION AGENT
# =====================================================

class CourseTopic(db.Model):
    __tablename__ = "course_topics"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True)

    topic_name = db.Column(db.Text, nullable=False)
    difficulty_level = db.Column(db.Text)

    course = db.relationship("Course", back_populates="topics")
    materials = db.relationship("LearningMaterial", back_populates="topic", cascade="all, delete-orphan")
    gaps = db.relationship("KnowledgeGap", back_populates="topic", cascade="all, delete-orphan")


class LearningMaterial(db.Model):
    __tablename__ = "learning_materials"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    topic_id = db.Column(UUID(as_uuid=True), db.ForeignKey("course_topics.id"), nullable=False, index=True)

    content = db.Column(db.Text)
    content_type = db.Column(db.String(50))
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    topic = db.relationship("CourseTopic", back_populates="materials")


class GeneratedContent(db.Model):
    __tablename__ = "generated_content"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    topic_id = db.Column(UUID(as_uuid=True), db.ForeignKey("course_topics.id"), nullable=False, index=True)

    content = db.Column(db.Text)
    difficulty_adjusted = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)


# =====================================================
# KNOWLEDGE GAP TRACKING
# =====================================================

class KnowledgeGap(db.Model):
    __tablename__ = "knowledge_gaps"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    topic_id = db.Column(UUID(as_uuid=True), db.ForeignKey("course_topics.id"), nullable=False, index=True)

    mastery_level = db.Column(db.Float, default=0.0, nullable=False)  # 0–1 or 0–100; pick one convention
    last_updated = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    topic = db.relationship("CourseTopic", back_populates="gaps")


# =====================================================
# INTERVENTION AGENT
# =====================================================

class StudentActivity(db.Model):
    __tablename__ = "student_activity"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True)

    activity_type = db.Column(db.String(100), nullable=False)
    time_spent_minutes = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    student = db.relationship("User", back_populates="activities")
    course = db.relationship("Course", back_populates="activities")


class InterventionLog(db.Model):
    __tablename__ = "intervention_logs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True)

    risk_level = db.Column(db.String(20))  # e.g., low/medium/high
    intervention_type = db.Column(db.String(100))
    triggered_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    course = db.relationship("Course", back_populates="interventions")


# =====================================================
# ACADEMIC INTEGRITY AGENT
# =====================================================

class PlagiarismReport(db.Model):
    __tablename__ = "plagiarism_reports"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    submission_id = db.Column(UUID(as_uuid=True), db.ForeignKey("submissions.id"), nullable=False, index=True)

    similarity_score = db.Column(db.Float)
    flagged = db.Column(db.Boolean, default=False, nullable=False)
    checked_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    submission = db.relationship("Submission", back_populates="plagiarism_reports")


class ExamBehaviorLog(db.Model):
    __tablename__ = "exam_behavior_logs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)

    assessment_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    ip_address = db.Column(db.String(100))
    keystroke_pattern = db.Column(JSONB)
    suspicious_activity = db.Column(db.Boolean, default=False, nullable=False)
    recorded_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class IntegrityScore(db.Model):
    __tablename__ = "integrity_scores"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    submission_id = db.Column(UUID(as_uuid=True), db.ForeignKey("submissions.id"), nullable=False, index=True)

    integrity_score = db.Column(db.Float)
    action_taken = db.Column(db.String(100))
    evaluated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    submission = db.relationship("Submission", back_populates="integrity_scores")


# =====================================================
# AI ANALYTICS
# =====================================================

class LearningAnalytics(db.Model):
    __tablename__ = "learning_analytics"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True)

    predicted_success_probability = db.Column(db.Float)
    dropout_risk = db.Column(db.Float)
    recommended_action = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    course = db.relationship("Course", back_populates="analytics")


# =====================================================
# VECTOR DATABASE FOR RAG (TEMP: JSONB)
# =====================================================

class ContentEmbedding(db.Model):
    __tablename__ = "content_embeddings"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    content_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    embedding = db.Column(JSONB, nullable=False)  # TEMP: store as JSON array of floats
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)