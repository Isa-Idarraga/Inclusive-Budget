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
from unittest.mock import patch

# Import the view
from dashboard.views import kpis_data

# Build a fake request and fake user (authenticated)
factory = RequestFactory()
req = factory.get('/jefe/kpis/data/')
req.user = SimpleNamespace(is_authenticated=True, is_superuser=False, role='JEFE')

# Patch Project and Material to avoid heavy DB access; return empty iterables
class FakeQS(list):
    def aggregate(self, **kw):
        return {'total_presupuesto': 0, 'total_gastado': 0}

with patch('dashboard.views.Project') as MockProject, patch('dashboard.views.Material') as MockMaterial:
    MockProject.objects.filter.return_value = FakeQS()
    MockMaterial.objects.filter.return_value = []

    resp = kpis_data(req)
    print('STATUS:', resp.status_code)
    # JsonResponse on server side has .content (bytes); decode and parse
    import json
    try:
        data = json.loads(resp.content.decode('utf-8'))
        print('JSON:', data)
    except Exception as e:
        print('Could not decode JSON:', e)
