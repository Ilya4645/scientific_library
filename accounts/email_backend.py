"""
Email бэкенды для отправки писем
Поддерживает: console, file, dummy
"""

import os
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string

class FileEmailBackend:
    """Бэкенд для сохранения писем в файлы"""

    def __init__(self):
        # Получаем путь из настроек - ВАЖНО: преобразуем в строку
        email_dir_setting = getattr(settings, 'EMAIL_FILE_PATH', None)

        if email_dir_setting:
            # Если это строка, используем как есть
            if isinstance(email_dir_setting, str):
                self.email_dir = email_dir_setting
            # Если это Path объект, преобразуем в строку
            else:
                self.email_dir = str(email_dir_setting)
        else:
            # Путь по умолчанию
            self.email_dir = os.path.join(settings.BASE_DIR, 'emails')

        self.file_format = getattr(settings, 'EMAIL_FILE_FORMAT', 'both')

        # Создаем папку для писем, если её нет
        os.makedirs(self.email_dir, exist_ok=True)

        print(f"📁 Email бэкенд инициализирован. Папка для писем: {self.email_dir}")

    def send_mail(self, subject, message, from_email, recipient_list, html_message=None):
        """Сохранение письма в файл"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        recipients = '_'.join([r.replace('@', '_at_').replace('.', '_dot_') for r in recipient_list])
        filename = f"{timestamp}_{recipients}"

        saved_files = []

        # Сохраняем текстовую версию
        if self.file_format in ['txt', 'both']:
            txt_path = os.path.join(self.email_dir, f"{filename}.txt")
            content = self._format_txt_email(subject, message, from_email, recipient_list, html_message)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            saved_files.append(txt_path)
            print(f"✅ Сохранено TXT: {txt_path}")

        # Сохраняем HTML версию
        if self.file_format in ['html', 'both'] and html_message:
            html_path = os.path.join(self.email_dir, f"{filename}.html")
            content = self._format_html_email(subject, html_message, from_email, recipient_list)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            saved_files.append(html_path)
            print(f"✅ Сохранено HTML: {html_path}")

        print(f"\n📧 Письмо для {', '.join(recipient_list)} сохранено в: {', '.join(saved_files)}\n")

        return True

    def _format_txt_email(self, subject, message, from_email, recipient_list, html_message=None):
        """Форматирование текстовой версии письма"""
        content = f"""
{'='*80}
EMAIL СОХРАНЕН: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

ОТ: {from_email}
КОМУ: {', '.join(recipient_list)}
ТЕМА: {subject}

{'='*80}
ТЕКСТОВОЕ СОДЕРЖАНИЕ:
{'='*80}

{message}

"""

        return content

    def _format_html_email(self, subject, html_message, from_email, recipient_list):
        """Форматирование HTML версии письма"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{subject}</title>
</head>
<body>
    <div style="background: #f0f0f0; padding: 10px; margin-bottom: 20px; font-family: monospace;">
        <strong>ОТ:</strong> {from_email}<br>
        <strong>КОМУ:</strong> {', '.join(recipient_list)}<br>
        <strong>ДАТА:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>ТЕМА:</strong> {subject}
    </div>
    <hr>
    {html_message}
    <hr>
    <div style="background: #fff3cd; padding: 10px; margin-top: 20px; font-size: 12px; color: #856404;">
        ⚠️ Это письмо создано в режиме разработки (файловый бэкенд)<br>
        Папка для писем: {self.email_dir}
    </div>
</body>
</html>"""


class DummyEmailBackend:
    """Пустой бэкенд - ничего не делает"""

    def send_mail(self, subject, message, from_email, recipient_list, html_message=None):
        """Ничего не делать"""
        print(f"[Dummy] Письмо для {recipient_list} с темой '{subject}' не отправлено (dummy режим)")
        return True


def get_email_backend():
    """Фабрика для получения бэкенда email на основе настроек"""
    backend_type = getattr(settings, 'EMAIL_BACKEND_TYPE', 'console')

    backends = {
        'file': FileEmailBackend,
        'dummy': DummyEmailBackend,
    }

    backend_class = backends.get(backend_type)
    print(f"🔧 Используется email бэкенд: {backend_type}")
    return backend_class()


def send_email(subject, message, recipient_list, html_message=None, from_email=None):
    """
    Универсальная функция отправки email
    """
    if from_email is None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    backend = get_email_backend()
    return backend.send_mail(subject, message, from_email, recipient_list, html_message)