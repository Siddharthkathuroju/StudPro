from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Setup chatbot configuration and API key'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Gemini API key to set',
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'],
            default='gemini-1.5-flash',
            help='Gemini model to use (default: gemini-1.5-flash)',
        )
        parser.add_argument(
            '--check-quota',
            action='store_true',
            help='Check current API quota status',
        )

    def handle(self, *args, **options):
        if options['check_quota']:
            self.check_quota()
            return

        api_key = options['api_key']
        model = options['model']

        if api_key:
            self.setup_api_key(api_key)
        
        self.display_info(model)

    def setup_api_key(self, api_key):
        """Set up the API key in .env file"""
        env_file = '.env'
        
        # Check if .env file exists
        if os.path.exists(env_file):
            # Read existing content
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Update or add GEMINI_API_KEY
            key_found = False
            for i, line in enumerate(lines):
                if line.startswith('GEMINI_API_KEY='):
                    lines[i] = f'GEMINI_API_KEY={api_key}\n'
                    key_found = True
                    break
            
            if not key_found:
                lines.append(f'GEMINI_API_KEY={api_key}\n')
            
            # Write back to file
            with open(env_file, 'w') as f:
                f.writelines(lines)
        else:
            # Create new .env file
            with open(env_file, 'w') as f:
                f.write(f'GEMINI_API_KEY={api_key}\n')
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ API key set successfully in {env_file}')
        )

    def check_quota(self):
        """Check current quota status"""
        self.stdout.write(self.style.WARNING('📊 Quota Information:'))
        self.stdout.write('')
        self.stdout.write('Free Tier Limits:')
        self.stdout.write('  • 15 requests per day')
        self.stdout.write('  • 60 requests per minute')
        self.stdout.write('  • Input token limits per minute')
        self.stdout.write('')
        self.stdout.write('Paid Tier (Gemini 1.5 Pro):')
        self.stdout.write('  • 1,000 requests per minute')
        self.stdout.write('  • Higher token limits')
        self.stdout.write('')
        self.stdout.write('To check your current usage:')
        self.stdout.write('  • Visit: https://aistudio.google.com/')
        self.stdout.write('  • Go to API Keys section')
        self.stdout.write('  • Check usage metrics')

    def display_info(self, model):
        """Display setup information"""
        self.stdout.write(self.style.SUCCESS('🤖 StudPro Chatbot Setup'))
        self.stdout.write('')
        
        # Check if API key is configured
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key:
            self.stdout.write(f'✅ API Key: Configured')
        else:
            self.stdout.write(self.style.ERROR('❌ API Key: Not configured'))
            self.stdout.write('   Run: python manage.py setup_chatbot --api-key YOUR_KEY')
        
        self.stdout.write(f'🤖 Model: {model}')
        self.stdout.write('')
        
        self.stdout.write('📋 Model Comparison:')
        self.stdout.write('  gemini-1.5-flash: Fast, efficient, good for most tasks')
        self.stdout.write('  gemini-1.5-pro:   More capable, better reasoning')
        self.stdout.write('  gemini-1.0-pro:   Older but still reliable')
        self.stdout.write('')
        
        self.stdout.write('💡 Tips:')
        self.stdout.write('  • Use gemini-1.5-flash for better quota efficiency')
        self.stdout.write('  • Monitor your usage at https://aistudio.google.com/')
        self.stdout.write('  • Consider upgrading to paid plan for unlimited access')
        self.stdout.write('')
        
        self.stdout.write('🔧 Commands:')
        self.stdout.write('  python manage.py setup_chatbot --api-key YOUR_KEY')
        self.stdout.write('  python manage.py setup_chatbot --check-quota')
        self.stdout.write('  python manage.py setup_chatbot --model gemini-1.5-flash') 