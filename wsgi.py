# wsgi.py

from app import create_app

app = create_app()

# For Vercel runtime
handler = app 
