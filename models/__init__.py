from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .course import (
    Course,
    Lesson,
    Enrollment,
    CourseTopic,
    LearningMaterial,
    GeneratedContent,
    KnowledgeGap,
    StudentActivity,
    InterventionLog,
    LearningAnalytics,
    ContentEmbedding,
)
from .assignment import Assignment
from .submission import Submission, PlagiarismReport, ExamBehaviorLog, IntegrityScore

__all__ = [
    "db",
    "User",
    "Course",
    "Lesson",
    "Enrollment",
    "Assignment",
    "Submission",
    "CourseTopic",
    "LearningMaterial",
    "GeneratedContent",
    "KnowledgeGap",
    "StudentActivity",
    "InterventionLog",
    "PlagiarismReport",
    "ExamBehaviorLog",
    "IntegrityScore",
    "LearningAnalytics",
    "ContentEmbedding",
]
