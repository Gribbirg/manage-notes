# Docker Deployment Instructions

This document provides instructions for deploying the Notes Manager application using Docker and Docker Compose.

## Prerequisites

- Docker installed on your server
- Docker Compose installed on your server
- Git (to clone the repository)

## Deployment Steps

### 1. Clone the repository

```bash
git clone https://github.com/gribbirg/manage-notes.git
cd manage-notes
```

### 2. Configure environment variables (Optional)

You can modify the environment variables in the `docker-compose.yml` file directly or create a `.env` file for more security.

### 3. Create required directories

```bash
mkdir -p nginx/conf.d
```

### 4. Start the services

```bash
docker-compose up -d
```

This command will:
- Build the application container
- Start the MySQL database
- Start the Nginx web server
- Configure the application

### 5. Create a superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

## Accessing the Application

The application will be available at: http://localhost or http://your-server-ip

The admin interface is available at: http://localhost/admin or http://your-server-ip/admin

## Maintenance

### Viewing logs

```bash
# View all logs
docker-compose logs

# View logs for a specific service
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```

### Stopping the services

```bash
docker-compose down
```

### Rebuilding the application after changes

```bash
docker-compose build web
docker-compose up -d
```

### Backing up the database

```bash
docker-compose exec db mysqldump -u notes_user -pnotes_password notes_db > backup.sql
```

## Security Considerations

For production deployment:

1. Change all default passwords in the `docker-compose.yml` file
2. Generate a proper `SECRET_KEY` value
3. Configure proper `ALLOWED_HOSTS` with your domain name
4. Consider setting up HTTPS with Let's Encrypt
5. Restrict database access to only the application container 