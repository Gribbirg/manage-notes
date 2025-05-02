from django.test import TestCase
from django.contrib.auth.models import User

from apps.notes.models import Category, Tag
from apps.notes.forms import NoteForm, CategoryForm, TagForm


class CategoryFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        Category.objects.create(
            name='Existing Category',
            user=self.user
        )

    def test_valid_category_form(self):
        """Test that form is valid with new category name"""
        form_data = {
            'name': 'New Category',
        }
        form = CategoryForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_duplicate_name(self):
        """Test that form is invalid with duplicate category name"""
        form_data = {
            'name': 'Existing Category',
        }
        form = CategoryForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_invalid_with_empty_name(self):
        """Test that form is invalid with empty name"""
        form_data = {
            'name': '',
        }
        form = CategoryForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class TagFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        Tag.objects.create(
            name='existingtag',
            user=self.user
        )

    def test_valid_tag_form(self):
        """Test that form is valid with new tag name"""
        form_data = {
            'name': 'newtag',
        }
        form = TagForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_duplicate_name(self):
        """Test that form is invalid with duplicate tag name"""
        form_data = {
            'name': 'existingtag',
        }
        form = TagForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_invalid_with_special_characters(self):
        """Test that form is invalid with special characters"""
        form_data = {
            'name': 'invalid!tag',
        }
        form = TagForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors) 