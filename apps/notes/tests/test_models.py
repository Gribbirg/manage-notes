from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from apps.notes.models import Category, Tag, Note, NoteSharing


class CategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )

    def test_category_creation(self):
        """Test category creation"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.user, self.user)
        self.assertTrue(isinstance(self.category, Category))
        self.assertEqual(str(self.category), 'Test Category')

    def test_category_unique_constraint(self):
        """Test that categories must be unique per user"""
        duplicate_category = Category(name='Test Category', user=self.user)
        with self.assertRaises(ValidationError):
            duplicate_category.full_clean()

class TagModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.tag = Tag.objects.create(
            name='testtag',
            user=self.user
        )

    def test_tag_creation(self):
        """Test tag creation"""
        self.assertEqual(self.tag.name, 'testtag')
        self.assertEqual(self.tag.user, self.user)
        self.assertTrue(isinstance(self.tag, Tag))
        self.assertEqual(str(self.tag), 'testtag')

    def test_tag_unique_constraint(self):
        """Test that tags must be unique per user"""
        duplicate_tag = Tag(name='testtag', user=self.user)
        with self.assertRaises(ValidationError):
            duplicate_tag.full_clean()


class NoteModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.tag1 = Tag.objects.create(
            name='tag1',
            user=self.user
        )
        self.tag2 = Tag.objects.create(
            name='tag2',
            user=self.user
        )
        self.note = Note.objects.create(
            title='Test Note',
            content='This is test content',
            category=self.category,
            user=self.user
        )
        self.note.tags.add(self.tag1, self.tag2)

    def test_note_creation(self):
        """Test note creation"""
        self.assertEqual(self.note.title, 'Test Note')
        self.assertEqual(self.note.content, 'This is test content')
        self.assertEqual(self.note.category, self.category)
        self.assertEqual(self.note.user, self.user)
        self.assertEqual(self.note.tags.count(), 2)
        self.assertTrue(isinstance(self.note, Note))
        self.assertEqual(str(self.note), 'Test Note')

    def test_note_get_excerpt(self):
        """Test the get_excerpt method of Note"""
        note = Note.objects.create(
            title='Long Content',
            content='This is a very long content that should be truncated',
            user=self.user
        )
        # Проверяем начало строки (символ многоточия может различаться)
        self.assertTrue(note.get_excerpt(10).startswith('This is a'))

    def test_note_with_wrong_category(self):
        """Test that a note cannot use a category from another user"""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword2'
        )
        category2 = Category.objects.create(
            name='Other Category',
            user=user2
        )
        
        note = Note(
            title='Invalid Note',
            content='This note should not validate',
            category=category2,
            user=self.user
        )
        
        with self.assertRaises(ValidationError):
            note.full_clean()

    def test_note_pin_functionality(self):
        """Test note pinning functionality"""
        self.assertFalse(self.note.is_pinned)
        self.note.is_pinned = True
        self.note.save()
        self.assertTrue(Note.objects.get(pk=self.note.pk).is_pinned)

class NoteSharingModelTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='password'
        )
        self.shared_user = User.objects.create_user(
            username='shared',
            email='shared@example.com',
            password='password'
        )
        self.note = Note.objects.create(
            title='Shared Note',
            content='This is shared content',
            user=self.owner
        )
        self.note_sharing = NoteSharing.objects.create(
            note=self.note,
            shared_with=self.shared_user,
            permission='read'
        )

    def test_note_sharing_creation(self):
        """Test note sharing creation"""
        self.assertEqual(self.note_sharing.note, self.note)
        self.assertEqual(self.note_sharing.shared_with, self.shared_user)
        self.assertEqual(self.note_sharing.permission, 'read')
        self.assertTrue(isinstance(self.note_sharing, NoteSharing))
        self.assertTrue(
            self.note_sharing.note.is_shared_with_user(self.shared_user)
        )

    def test_note_sharing_permissions(self):
        """Test note sharing permission methods"""
        # Owner should have owner permission
        self.assertEqual(self.note.get_user_permission(self.owner), 'owner')
        
        # Shared user should have read permission
        self.assertEqual(
            self.note.get_user_permission(self.shared_user), 'read'
        )
        
        # Owner can edit
        self.assertTrue(self.note.can_user_edit(self.owner))
        
        # Shared user with 'read' cannot edit
        self.assertFalse(self.note.can_user_edit(self.shared_user))
        
        # Change permission to 'edit'
        self.note_sharing.permission = 'edit'
        self.note_sharing.save()
        
        # Now shared user can edit
        self.assertTrue(self.note.can_user_edit(self.shared_user)) 