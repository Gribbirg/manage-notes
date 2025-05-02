# Import the test classes from test modules
from apps.notes.tests.test_models import (
    CategoryModelTest,
    TagModelTest,
    NoteModelTest,
    NoteSharingModelTest
)

from apps.notes.tests.test_forms import (
    CategoryFormTest,
    TagFormTest
)

from apps.notes.tests.test_views import (
    NoteViewsTest,
    CategoryViewsTest,
    TagViewsTest
)

from apps.notes.tests.test_api import (
    NoteAPITest,
    CategoryAPITest,
    TagAPITest
)

# Make all test classes available to the test runner
__all__ = [
    'CategoryModelTest',
    'TagModelTest',
    'NoteModelTest',
    'NoteSharingModelTest',
    'CategoryFormTest',
    'TagFormTest',
    'NoteViewsTest',
    'CategoryViewsTest',
    'TagViewsTest',
    'NoteAPITest',
    'CategoryAPITest',
    'TagAPITest'
]
