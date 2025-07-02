#!/usr/bin/env python
"""
Database setup script for StudPro Django application.
Run this script to create the database tables and set up initial data.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studpro.settings')
django.setup()

from django.core.management import execute_from_command_line

def setup_database():
    """Set up the database with migrations and create superuser."""
    print("Setting up StudPro database...")
    
    # Make migrations
    print("Creating migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # Apply migrations
    print("Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser (optional)
    print("\nDatabase setup complete!")
    print("To create a superuser, run: python manage.py createsuperuser")
    print("To start the development server, run: python manage.py runserver")

if __name__ == '__main__':
    setup_database()
