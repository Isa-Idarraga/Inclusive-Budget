import os
import sys
from types import SimpleNamespace

# Ensure we run from project root
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.test import RequestFactory

# Import the view
from dashboard.views import kpis_data

# Build a fake request and fake user (authenticated)
factory = RequestFactory()
req = factory.get('/jefe/kpis/data/')
req.user = SimpleNamespace(is_authenticated=True, is_superuser=False, role='JEFE')

resp = kpis_data(req)
print('STATUS:', resp.status_code)
import json
data = json.loads(resp.content.decode('utf-8'))
print('JSON:', data)
