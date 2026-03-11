import uuid

from sqlalchemy.dialects.postgresql import UUID

from . import db


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    course_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("courses.id"), nullable=False, index=True
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Float, default=100.0, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    generated_by_ai = db.Column(db.Boolean, default=False, nullable=False)

    course = db.relationship("Course", back_populates="assignments")
    submissions = db.relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )
