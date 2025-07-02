#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studpro.settings')
django.setup()

from django.conf import settings
import google.generativeai as genai

print("Testing chatbot configuration...")
print(f"Settings type: {type(settings)}")
print(f"GEMINI_API_KEY exists: {hasattr(settings, 'GEMINI_API_KEY')}")
print(f"GEMINI_API_KEY value: {getattr(settings, 'GEMINI_API_KEY', 'NOT_FOUND')[:10] + '...' if getattr(settings, 'GEMINI_API_KEY', '') else 'None'}")

if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Hello, this is a test.")
        print(f"Test response: {response.text}")
        print("✅ Chatbot is working correctly!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e)}")
else:
    print("❌ No API key found") 