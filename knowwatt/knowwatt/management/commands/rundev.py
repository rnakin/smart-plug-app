# management/commands/rundev.py
import subprocess
import sys
import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Run Django and Vue dev servers simultaneously'

    def handle(self, *args, **options):
        # path to your Vue project
        vue_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )), 'frontend_migrate')  # adjust this to your Vue folder name

        django = subprocess.Popen(
            [sys.executable, 'manage.py', 'runserver'],
        )
        vue = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=vue_dir,
        )

        try:
            django.wait()
        except KeyboardInterrupt:
            django.terminate()
            vue.terminate()