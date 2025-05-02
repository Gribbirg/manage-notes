.PHONY: test test-notes test-accounts lint coverage clean

# Run all tests
test:
	python manage.py test apps.accounts.tests
	python manage.py test apps.notes.tests.test_models apps.notes.tests.test_forms apps.notes.tests.test_views apps.notes.tests.test_api

# Run only notes app tests
test-notes:
	python manage.py test apps.notes.tests.test_models apps.notes.tests.test_forms apps.notes.tests.test_views apps.notes.tests.test_api

# Run only accounts app tests
test-accounts:
	python manage.py test apps.accounts.tests

# Run linting
lint:
	flake8 apps

# Run coverage tests
coverage:
	coverage run --source='apps' manage.py test apps
	coverage report -m
	coverage html

# Clean up pyc files and __pycache__ directories
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/ 