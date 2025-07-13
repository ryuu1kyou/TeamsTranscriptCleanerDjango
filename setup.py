#!/usr/bin/env python
"""
Setup script for Teams Transcript Cleaner Django project.
This script helps initialize the project quickly.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"   ✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False


def check_requirements():
    """Check if required software is installed."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("   ❌ Python 3.8+ is required")
        return False
    print(f"   ✅ Python {sys.version.split()[0]} found")
    
    # Check if pip is available
    try:
        import pip
        print(f"   ✅ pip is available")
    except ImportError:
        print("   ❌ pip is not available")
        return False
    
    return True


def setup_environment():
    """Set up virtual environment and install dependencies."""
    print("🐍 Setting up Python environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            return False
    else:
        print("   ✅ Virtual environment already exists")
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = os.path.join('venv', 'Scripts', 'pip')
        python_path = os.path.join('venv', 'Scripts', 'python')
    else:  # Unix/Linux/Mac
        pip_path = os.path.join('venv', 'bin', 'pip')
        python_path = os.path.join('venv', 'bin', 'python')
    
    # Install dependencies
    if not run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies"):
        return False
    
    return True, python_path


def setup_environment_file():
    """Create .env file from .env.example if it doesn't exist."""
    print("⚙️  Setting up environment configuration...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("   ✅ Created .env file from .env.example")
            print("   ⚠️  Please edit .env file with your configuration")
        else:
            # Create a basic .env file
            env_content = """# Django Settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True

# Database Configuration (MySQL)
DB_NAME=transcript_cleaner
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0
"""
            with open('.env', 'w') as f:
                f.write(env_content)
            print("   ✅ Created basic .env file")
            print("   ⚠️  Please edit .env file with your configuration")
    else:
        print("   ✅ .env file already exists")
    
    return True


def setup_database(python_path):
    """Set up database and run migrations."""
    print("🗄️  Setting up database...")
    
    os.chdir('transcript_cleaner')
    
    # Run migrations
    if not run_command(f"{python_path} manage.py makemigrations", "Creating migrations"):
        return False
    
    if not run_command(f"{python_path} manage.py migrate", "Running migrations"):
        return False
    
    # Create superuser (optional)
    print("👤 Creating superuser (optional)...")
    print("   You can skip this and use the test data instead")
    try:
        subprocess.run(f"{python_path} manage.py createsuperuser", shell=True, check=True)
        print("   ✅ Superuser created")
    except subprocess.CalledProcessError:
        print("   ⏭️  Superuser creation skipped")
    
    # Create test data
    if run_command(f"{python_path} manage.py create_test_data", "Creating test data"):
        print("   📝 Test accounts created:")
        print("      Admin: admin@example.com / admin123")
        print("      User:  test@example.com / test123")
    
    os.chdir('..')
    return True


def main():
    """Main setup function."""
    print("🚀 Teams Transcript Cleaner - Django Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('transcript_cleaner'):
        print("❌ This script must be run from the django project root directory")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements check failed")
        sys.exit(1)
    
    # Setup environment
    result = setup_environment()
    if not result:
        print("❌ Environment setup failed")
        sys.exit(1)
    
    success, python_path = result
    if not success:
        sys.exit(1)
    
    # Setup .env file
    if not setup_environment_file():
        print("❌ Environment file setup failed")
        sys.exit(1)
    
    # Setup database
    if not setup_database(python_path):
        print("❌ Database setup failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration (especially OPENAI_API_KEY)")
    print("2. If using MySQL, create the database first")
    print("3. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("4. Start the development server:")
    print("   cd transcript_cleaner")
    print("   python manage.py runserver")
    print("\n🌐 Access the application at: http://127.0.0.1:8000/")


if __name__ == '__main__':
    main()