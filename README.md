# Notes Manager

A simple Django application for managing personal notes.

## Features

- User authentication (local and Yandex OAuth)
- Create, read, update, and delete notes
- Categorize and tag notes
- Search and filter functionality
- Role-based access control
- REST API for programmatic access
- Export notes to CSV and JSON formats
- Interactive dashboard with statistics

## Technologies

- Backend: Django, Python
- Database: SQLite
- Frontend: Bootstrap
- API: Django REST Framework

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
5. Create a `.env` file in the project root and configure it based on `env_settings.py`
6. Run migrations:
   ```
   python manage.py migrate
   ```
7. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
8. Run the server:
   ```
   python manage.py runserver
   ```

## Yandex OAuth Setup

1. Register your application on [Yandex OAuth](https://oauth.yandex.com/)
2. Set the redirect URI to `http://localhost:8000/auth/complete/yandex-oauth2/`
3. Add your Yandex OAuth ID and Secret to the `.env` file

## API Usage

The application provides a RESTful API for programmatic access to notes, categories, and tags. See the API documentation at `/api/docs/` for details and examples.

## Export

The application supports exporting notes to PDF format using the ReportLab library. To use this feature:

1. Install ReportLab: `pip install reportlab==4.1.0`
2. Export is available through:
   - URL `/notes/export/pdf/` for exporting all notes
   - URL `/notes/export/pdf/?id=<note_id>` for exporting a specific note
   - Export buttons are available on the notes list, advanced search, and note detail pages

PDF files include the full content of notes, metadata (categories, tags, creation and update dates) and are formatted for easy reading.

## License

MIT 