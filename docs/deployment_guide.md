# Руководство по развертыванию Notes Manager на Ubuntu

Это руководство поможет вам развернуть проект Notes Manager на чистом сервере Ubuntu.

## 1. Обновите систему

```bash
sudo apt update
sudo apt upgrade -y
```

## 2. Установите необходимые пакеты

```bash
sudo apt install -y python3 python3-pip python3-venv git nginx python3-dev
```

## 3. Клонируйте репозиторий

```bash
cd /var/www
sudo mkdir notes-manager
sudo chown $USER:$USER notes-manager
git clone https://github.com/gribbirg/manage-notes.git notes-manager
cd notes-manager
```

## 4. Настройте виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## 5. Настройте переменные окружения

Создайте файл `.env` в корне проекта:

```bash
nano .env
```

Добавьте следующие параметры:

```
SECRET_KEY=ваш_секретный_ключ
DEBUG=False
ALLOWED_HOSTS=ваш_домен,IP_адрес,localhost
DATABASE_URL=sqlite:///db.sqlite3
```

## 6. Выполните миграции и соберите статические файлы

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 7. Настройте Gunicorn

Создайте файл сервиса systemd:

```bash
sudo nano /etc/systemd/system/notes.service
```

С содержимым:

```
[Unit]
Description=Notes Manager Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/notes-manager
ExecStart=/var/www/notes-manager/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/notes-manager/notes.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

## 8. Настройте Nginx

Создайте конфигурационный файл:

```bash
sudo nano /etc/nginx/sites-available/notes
```

С содержимым:

```
server {
    listen 80;
    server_name ваш_домен или_IP;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/notes-manager;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/notes-manager/notes.sock;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/notes /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 9. Настройте права доступа

```bash
sudo chown -R www-data:www-data /var/www/notes-manager
sudo chmod -R 755 /var/www/notes-manager
# Убедитесь, что файл базы данных доступен для записи
sudo chown www-data:www-data /var/www/notes-manager/db.sqlite3
sudo chmod 664 /var/www/notes-manager/db.sqlite3
sudo chown www-data:www-data /var/www/notes-manager
sudo chmod 775 /var/www/notes-manager
```

## 10. Запустите сервис Gunicorn

```bash
sudo systemctl start notes
sudo systemctl enable notes
```

## 11. Настройте брандмауэр

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

## Проверка развертывания

Теперь ваше приложение должно быть доступно по адресу: http://ваш_домен или http://ваш_IP

## Обновление приложения

Для обновления приложения выполните следующие команды:

```bash
cd /var/www/notes-manager
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart notes
```

## Устранение неполадок

### Проверка логов

```bash
# Логи Gunicorn
sudo journalctl -u notes

# Логи Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Перезапуск сервисов

```bash
sudo systemctl restart notes
sudo systemctl restart nginx
``` 