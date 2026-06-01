"""
WSGI config for scientific_library project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Путь к проекту
project_path = '/home/ilya323/scientific-library'
sys.path.insert(0, project_path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scientific_library.settings')

application = get_wsgi_application()
