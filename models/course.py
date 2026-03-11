import uuid

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from . import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(20), unique=True, index=True)

    instructor_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)

    instructor = db.relationship("User", back_populates="courses_taught")
    lessons = db.relationship(
        "Lesson", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )
    assignments = db.relationship(
        "Assignment", back_populates="course", cascade="all, delete-orphan"
    )
    topics = db.relationship(
        "CourseTopic", back_populates="course", cascade="all, delete-orphan"
    )
    activities = db.relationship(
        "StudentActivity", back_populates="course", cascade="all, delete-orphan"
    )
    interventions = db.relationship(
        "InterventionLog", back_populates="course", cascade="all, delete-orphan"
    )
    analytics = db.relationship(
        "LearningAnalytics", back_populates="course", cascade="all, delete-orphan"
    )


class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    course_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True
    )

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=0, nullable=False)
    video_url = db.Column(db.String(500))
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)

    course = db.relationship("Course", back_populates="lessons")


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )
    course_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True
    )

    enrolled_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    progress = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)

    user = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
    )


class CourseTopic(db.Model):
    __tablename__ = "course_topics"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    course_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True
    )

    topic_name = db.Column(db.Text, nullable=False)
    difficulty_level = db.Column(db.Text)

    course = db.relationship("Course", back_populates="topics")
    materials = db.relationship(
        "LearningMaterial", back_populates="topic", cascade="all, delete-orphan"
    )
    gaps = db.relationship(
        "KnowledgeGap", back_populates="topic", cascade="all, delete-orphan"
    )


class LearningMaterial(db.Model):
    __tablename__ = "learning_materials"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    topic_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("course_topics.id"),
        nullable=False,
        index=True,
    )

    content = db.Column(db.Text)
    content_type = db.Column(db.String(50))
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    topic = db.relationship("CourseTopic", back_populates="materials")


class GeneratedContent(db.Model):
    __tablename__ = "generated_content"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    student_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )
    topic_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("course_topics.id"),
        nullable=False,
        index=True,
    )

    content = db.Column(db.Text)
    difficulty_adjusted = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class KnowledgeGap(db.Model):
    __tablename__ = "knowledge_gaps"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    student_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )
    topic_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("course_topics.id"),
        nullable=False,
        index=True,
    )

    mastery_level = db.Column(db.Float, default=0.0, nullable=False)
    last_updated = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    topic = db.relationship("CourseTopic", back_populates="gaps")


class StudentActivity(db.Model):
    __tablename__ = "student_activity"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    student_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )
    course_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True
    )

    activity_type = db.Column(db.String(100), nullable=False)
    time_spent_minutes = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    student = db.relationship("User", back_populates="activities")
    course = db.relationship("Course", back_populates="activities")


class InterventionLog(db.Model):
    __tablename__ = "intervention_logs"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    student_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )
    course_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True
    )

    risk_level = db.Column(db.String(20))
    intervention_type = db.Column(db.String(100))
    triggered_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    course = db.relationship("Course", back_populates="interventions")


class LearningAnalytics(db.Model):
    __tablename__ = "learning_analytics"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    student_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )
    course_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True
    )

    predicted_success_probability = db.Column(db.Float)
    dropout_risk = db.Column(db.Float)
    recommended_action = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    course = db.relationship("Course", back_populates="analytics")


class ContentEmbedding(db.Model):
    __tablename__ = "content_embeddings"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    content_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    embedding = db.Column(JSONB, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
