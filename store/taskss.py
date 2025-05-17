import requests
import logging
from celery import shared_task
from django.utils.timezone import now, localtime
from .models import ChannelMessage
from store.models import TelegramBotToken
import os
import shutil
import datetime
import tempfile
import subprocess
import requests
import logging
from celery import shared_task
from store.models import TelegramBotToken
from django.conf import settings



@shared_task
def backup_project_and_send():
    try:
        # Read from environment or Django settings
        db_name = os.environ['DB_NAME']
        db_user = os.environ['DB_USER']
        db_password = os.environ['DB_PASSWORD']
        db_host = os.environ.get('DB_HOST', 'db')  # 'db' is the common Docker service name
        db_port = os.environ.get('DB_PORT', '5432')

        telegram_token = TelegramBotToken.objects.first().token
        telegram_user_id = '185097996'  # Add this to .env
        if not telegram_user_id:
            logging.warning("⚠️ No BACKUP_TELEGRAM_USER_ID specified.")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['PGPASSWORD'] = db_password  # Needed for pg_dump authentication

            backup_path = os.path.join(tmpdir, 'db_backup.sql')

            result = subprocess.run([
                'pg_dump',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-f', backup_path,
                db_name
            ], check=True)

            # Send to Telegram
            with open(backup_path, 'rb') as f:
                response = requests.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendDocument",
                    data={'chat_id': telegram_user_id, 'caption': '📦 DB Backup'},
                    files={'document': f}
                )
                if response.status_code != 200:
                    logging.error(f"Telegram send error: {response.text}")

    except Exception as e:
        logging.error(f"❌ Exception in backup task: {e}")