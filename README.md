# StudPro - Student Productivity Platform

StudPro is a comprehensive Django web application designed to help students manage their academic life effectively.

## Features

- **User Authentication**: Secure signup/signin system
- **Profile Management**: Customizable user profiles with avatars
- **Study Groups**: Create and join study groups with other students
- **AI Chatbot**: Integrated Gemini AI assistant for academic help
- **Learning Tracks**: Create and track learning progress
- **File Management**: Upload and organize study materials
- **Responsive Design**: Modern UI with Tailwind CSS

## Installation

1. **Clone the repository**
   \`\`\`bash
   git clone <repository-url>
   cd studpro
   \`\`\`

2. **Create a virtual environment**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`

3. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Set up environment variables**
   \`\`\`bash
   export GEMINI_API_KEY="your-gemini-api-key-here"
   \`\`\`

5. **Set up the database**
   \`\`\`bash
   python scripts/setup_database.py
   \`\`\`

6. **Create a superuser (optional)**
   \`\`\`bash
   python manage.py createsuperuser
   \`\`\`

7. **Run the development server**
   \`\`\`bash
   python manage.py runserver
   \`\`\`

## Usage

1. **Sign Up**: Create a new account at `/signup/`
2. **Sign In**: Log in to your account at `/signin/`
3. **Dashboard**: Access your personalized dashboard after login
4. **Profile**: Update your profile information and avatar
5. **Groups**: Create or join study groups
6. **Chatbot**: Get AI assistance with your studies
7. **Learning Tracks**: Create and monitor your learning progress
8. **Files**: Upload and manage your study materials

## Configuration

### Gemini AI Integration

To use the chatbot feature, you need to:

1. Get a Gemini API key from Google AI Studio
2. Set the `GEMINI_API_KEY` environment variable
3. The chatbot will be available at `/chatbot/`

### File Uploads

- Files are stored in the `media/uploads/` directory
- Supported file types: documents, images, videos
- File size limits can be configured in Django settings

## Project Structure

\`\`\`
studpro/
├── manage.py
├── studpro/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── main/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── registration/
│   └── main/
├── static/
├── media/
└── scripts/
\`\`\`

## Models

- **UserProfile**: Extended user information
- **Group**: Study groups with members
- **LearningTrack**: Progress tracking for learning goals
- **UploadedFile**: File management system
- **ChatMessage**: Chat history with AI assistant

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
