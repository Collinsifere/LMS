#!/usr/bin/env python3
"""
Setup script to create necessary directories for the LMS
Run this after cloning/downloading the project
"""

import os

# Directories to create
directories = [
    'static',
    'static/css',
    'static/js',
    'static/images',
    'uploads',
    'templates',
    'templates/auth',
    'templates/courses',
    'templates/dashboard',
    'templates/assignments',
    'routes'
]

def setup_directories():
    """Create all necessary directories"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    print("Creating directory structure...")
    
    for directory in directories:
        dir_path = os.path.join(base_path, directory)
        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✓ Created: {directory}/")
        else:
            print(f"⚠ Already exists: {directory}/")
    
    # Create __init__.py in routes folder
    routes_init = os.path.join(base_path, 'routes', '__init__.py')
    if not os.path.exists(routes_init):
        with open(routes_init, 'w') as f:
            f.write('# Routes package\n')
        print("✓ Created: routes/__init__.py")
    
    # Create a placeholder CSS file
    css_file = os.path.join(base_path, 'static/css', 'style.css')
    if not os.path.exists(css_file):
        with open(css_file, 'w') as f:
            f.write('''/* Custom styles for LMS */

body {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

main {
    flex: 1;
}

.card {
    margin-bottom: 1.5rem;
}

.course-card {
    transition: transform 0.2s;
}

.course-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
''')
        print("✓ Created: static/css/style.css")
    
    # Create a placeholder JS file
    js_file = os.path.join(base_path, 'static/js', 'main.js')
    if not os.path.exists(js_file):
        with open(js_file, 'w') as f:
            f.write('''// Custom JavaScript for LMS

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });
});
''')
        print("✓ Created: static/js/main.js")
    
    # Create .gitkeep in uploads to track empty folder
    gitkeep = os.path.join(base_path, 'uploads', '.gitkeep')
    if not os.path.exists(gitkeep):
        with open(gitkeep, 'w') as f:
            f.write('')
        print("✓ Created: uploads/.gitkeep")
    
    print("\n✅ Setup complete! Directory structure is ready.")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Copy .env.example to .env and configure")
    print("3. Create HTML templates in the templates/ folder")
    print("4. Run the application: python app.py")

if __name__ == '__main__':
    setup_directories()
