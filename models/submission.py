import uuid

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from . import db


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    assignment_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("assignments.id"), nullable=False, index=True
    )
    student_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )

    content = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    graded_at = db.Column(db.DateTime)

    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship("User", back_populates="submissions")

    plagiarism_reports = db.relationship(
        "PlagiarismReport", back_populates="submission", cascade="all, delete-orphan"
    )
    integrity_scores = db.relationship(
        "IntegrityScore", back_populates="submission", cascade="all, delete-orphan"
    )


class PlagiarismReport(db.Model):
    __tablename__ = "plagiarism_reports"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    submission_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("submissions.id"), nullable=False, index=True
    )

    similarity_score = db.Column(db.Float)
    flagged = db.Column(db.Boolean, default=False, nullable=False)
    checked_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    submission = db.relationship("Submission", back_populates="plagiarism_reports")


class ExamBehaviorLog(db.Model):
    __tablename__ = "exam_behavior_logs"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    student_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True
    )

    assessment_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    ip_address = db.Column(db.String(100))
    keystroke_pattern = db.Column(JSONB)
    suspicious_activity = db.Column(db.Boolean, default=False, nullable=False)
    recorded_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)


class IntegrityScore(db.Model):
    __tablename__ = "integrity_scores"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    submission_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("submissions.id"), nullable=False, index=True
    )

    integrity_score = db.Column(db.Float)
    action_taken = db.Column(db.String(100))
    evaluated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    submission = db.relationship("Submission", back_populates="integrity_scores")
