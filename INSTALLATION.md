# Installation Guide

## Requirements

* Python 3.8+
* pip
* virtualenv (optional but recommended)
* MySQL/MariaDB or SQLite

## Installation Steps

### 1. Clone the repository

```bash
git clone <repository-url>
cd manage-notes
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

#### Windows
```
venv\Scripts\activate
```

#### macOS/Linux
```
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the database

Create a `.env` file in the project root and add the following parameters:

```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

For MySQL/MariaDB:
```
DATABASE_URL=mysql://user:password@localhost:3306/dbname
```

### 6. Run database migrations

```bash
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Start the development server

```bash
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

## Additional Components

### PDF Export

For exporting notes to PDF format, the application uses the ReportLab library, which is already included in `requirements.txt`. If you're installing dependencies manually, run:

```bash
pip install reportlab==4.1.0
```

## Testing

### Running tests

```bash
python manage.py test
```

### Testing PDF Functionality

To verify PDF export functionality, you can use the following URLs:

1. Export all notes: `/notes/export/pdf/`
2. Export a single note: `/notes/export/pdf/?id=1` (replace 1 with an existing note ID)
3. Export with filtering: `/notes/export/pdf/?query=test&category=1`

## Troubleshooting

### ReportLab installation errors

If you encounter issues when installing ReportLab, make sure you have the necessary system dependencies:

#### Windows
```
pip install --upgrade pip setuptools wheel
```

#### Ubuntu/Debian
```
sudo apt-get install python3-dev libjpeg-dev zlib1g-dev
```

#### macOS
```
brew install libjpeg zlib
``` 