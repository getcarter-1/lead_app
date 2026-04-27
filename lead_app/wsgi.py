import sys, os
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)
os.environ.setdefault('FLASK_ENV', 'production')
from app import create_app
application = create_app('production')
