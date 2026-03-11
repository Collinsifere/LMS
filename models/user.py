from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import uuid

from sqlalchemy.dialects.postgresql import UUID

from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False, index=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    learning_style = db.Column(db.String(50))
    skill_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    enrollments = db.relationship(
        "Enrollment", back_populates="user", cascade="all, delete-orphan"
    )
    courses_taught = db.relationship("Course", back_populates="instructor")
    submissions = db.relationship("Submission", back_populates="student")
    activities = db.relationship("StudentActivity", back_populates="student")

    def get_id(self):
        return str(self.id)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
