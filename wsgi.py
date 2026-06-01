# scientific_library/wsgi.py
import os
import sys

# Добавляем путь к проекту
path = 'C:/Users/Admin/Dropbox/scientific_library'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scientific_library.settings')

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

application = get_wsgi_application()
application = WhiteNoise(application, root=os.path.join(path, 'staticfiles'))