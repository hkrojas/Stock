import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-for-dev'
    API_BASE_URL = os.environ.get('API_BASE_URL') or 'http://localhost:8000/api/v1'
    API_ROOT_URL = API_BASE_URL.rsplit('/api/', 1)[0] if '/api/' in API_BASE_URL else API_BASE_URL.rstrip('/')
    API_DOCS_URL = f'{API_ROOT_URL}/docs'
