# 🤖 StudPro Chatbot Setup Guide

## Overview
The StudPro chatbot uses Google's Gemini AI to provide intelligent study assistance. It can help with homework, study tips, research, and general academic questions.

## Setup Instructions

### 1. Get a Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 2. Install Required Package
```bash
pip install python-dotenv
```

### 3. Set Up the API Key

#### Option A: Using the Management Command (Recommended)
```bash
python manage.py setup_chatbot --api-key YOUR_API_KEY_HERE
```

#### Option B: Manual Setup
1. Create a `.env` file in your project root (same level as `manage.py`)
2. Add this line to the `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### 4. Restart Your Server
```bash
python manage.py runserver
```

## Features

### ✨ Enhanced Chatbot Interface
- **Modern UI**: Beautiful, responsive design with gradient headers
- **Typing Indicators**: Shows when the AI is thinking
- **Message Timestamps**: Track when messages were sent
- **Character Counter**: Prevents overly long messages
- **Quick Actions**: Pre-defined study-related prompts
- **Error Handling**: User-friendly error messages

### 🧠 Smart Responses
- **Context-Aware**: Knows your name and provides personalized responses
- **Study-Focused**: Optimized for academic assistance
- **Educational**: Provides helpful explanations and tips
- **Encouraging**: Supportive and motivating responses

### 📱 User Experience
- **Real-time Chat**: Instant message sending and receiving
- **Message History**: View your previous conversations
- **Responsive Design**: Works on desktop and mobile
- **Accessibility**: Keyboard navigation and screen reader friendly

## Usage

1. **Navigate to Chatbot**: Click "Chatbot" in the sidebar
2. **Start Chatting**: Type your question or use quick action buttons
3. **Get Help**: Ask about:
   - Study techniques and tips
   - Homework assistance
   - Research help
   - Learning strategies
   - General knowledge questions

## Troubleshooting

### API Key Issues
- **Error**: "AI service authentication issue"
  - **Solution**: Check your API key is correct and properly set

### Connection Issues
- **Error**: "Trouble connecting to AI service"
  - **Solution**: Check your internet connection

### Rate Limiting
- **Error**: "Usage limit reached"
  - **Solution**: Wait and try again later, or upgrade your API plan

### General Issues
- **Error**: "Unexpected error"
  - **Solution**: Refresh the page and try again

## Security Notes

- ✅ API keys are stored in environment variables (not in code)
- ✅ `.env` files should be added to `.gitignore`
- ✅ No sensitive data is logged or stored inappropriately
- ✅ All chat messages are associated with authenticated users

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your API key is working at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Check the Django console for error messages
4. Ensure all required packages are installed

---

**Happy Studying! 📚✨** 