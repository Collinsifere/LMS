# Learning Management System (LMS) - Python/Flask

A complete skeleton for building a Learning Management System using Python and Flask.

## Features

### User Roles
- **Students**: Enroll in courses, view lessons, submit assignments
- **Instructors**: Create courses, add lessons, create assignments, grade submissions
- **Admins**: Full access to all features

### Core Functionality
- User authentication (login, registration, logout)
- Course management (create, edit, view, publish)
- Lesson/module management
- Student enrollment
- Assignment creation and submission
- Assignment grading and feedback
- Progress tracking
- Role-based access control

## Project Structure

```
lms/
├── app.py                 # Main application entry point
├── models.py              # Database models
├── forms.py               # WTForms form definitions
├── requirements.txt       # Python dependencies
├── routes/
│   ├── auth.py           # Authentication routes
│   ├── courses.py        # Course management routes
│   ├── dashboard.py      # Dashboard routes
│   └── assignments.py    # Assignment routes
├── templates/            # HTML templates (to be created)
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   ├── student.html
│   │   └── instructor.html
│   ├── courses/
│   │   ├── index.html
│   │   ├── view.html
│   │   ├── create.html
│   │   └── create_lesson.html
│   └── assignments/
│       ├── view.html
│       ├── submit.html
│       └── grade.html
├── static/               # CSS, JS, images (to be created)
│   ├── css/
│   ├── js/
│   └── images/
└── uploads/              # File upload directory

```

## Database Models

### User
- Authentication and user profile
- Roles: student, instructor, admin
- Relationships to enrollments, courses, and submissions

### Course
- Course information and metadata
- Belongs to an instructor
- Contains lessons, enrollments, and assignments

### Lesson
- Course content modules
- Ordered lessons with text content and optional video

### Enrollment
- Links students to courses
- Tracks progress and status

### Assignment
- Course assignments with due dates
- Maximum score configuration

### Submission
- Student assignment submissions
- File uploads and text content
- Grading and feedback

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///lms.db
```

### 3. Initialize the Database

```bash
python app.py
```

The database will be created automatically on first run.

### 4. Create Templates Directory

Create the `templates/` directory structure as shown above and add your HTML templates.

### 5. Create Static Files Directory

Create the `static/` directory for CSS, JavaScript, and images.

### 6. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `GET/POST /auth/login` - User login
- `GET/POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Dashboard
- `GET /dashboard/` - Main dashboard (redirects based on role)
- `GET /dashboard/student` - Student dashboard
- `GET /dashboard/instructor` - Instructor dashboard

### Courses
- `GET /courses/` - List all courses
- `GET /courses/<id>` - View course details
- `GET/POST /courses/create` - Create new course (instructor only)
- `GET/POST /courses/<id>/edit` - Edit course (instructor only)
- `POST /courses/<id>/enroll` - Enroll in course (student)
- `GET/POST /courses/<id>/lessons/create` - Create lesson (instructor only)

### Assignments
- `GET/POST /assignments/course/<course_id>/create` - Create assignment (instructor)
- `GET /assignments/<id>` - View assignment
- `GET/POST /assignments/<id>/submit` - Submit assignment (student)
- `GET/POST /assignments/submission/<id>/grade` - Grade submission (instructor)

## Extending the System

### Adding New Features

1. **Quiz System**: Create Quiz and Question models, add quiz routes
2. **Discussion Forums**: Add Forum and Post models
3. **Certificates**: Generate completion certificates for students
4. **Analytics**: Track student progress and engagement
5. **Video Hosting**: Integrate with video platforms (YouTube, Vimeo)
6. **Email Notifications**: Add email alerts for assignments, grades
7. **Calendar**: Course calendar with important dates
8. **Live Classes**: Integration with video conferencing tools

### Customization

- Modify models in `models.py` to add fields
- Create new forms in `forms.py`
- Add routes in the appropriate blueprint
- Create corresponding templates

## Security Considerations

- Change the SECRET_KEY in production
- Use environment variables for sensitive data
- Implement CSRF protection (included with Flask-WTF)
- Add rate limiting for login attempts
- Validate and sanitize all user inputs
- Use HTTPS in production
- Implement proper file upload validation

## Database Migration

For production use, consider using Flask-Migrate for database migrations:

```bash
pip install Flask-Migrate
```

## Testing

Create a `tests/` directory and add unit tests:

```bash
pip install pytest pytest-flask
pytest
```

## Deployment

### Production Checklist
1. Set DEBUG=False
2. Use production database (PostgreSQL recommended)
3. Set strong SECRET_KEY
4. Configure proper logging
5. Set up static file serving (nginx/Apache)
6. Use WSGI server (gunicorn, uWSGI)
7. Enable HTTPS
8. Set up backups
9. Configure monitoring

### Example with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:create_app()
```

## License

MIT License - feel free to use this skeleton for your own projects.

## Contributing

This is a skeleton project meant to be customized. Fork and modify as needed for your use case.
