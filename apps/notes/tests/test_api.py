from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from apps.notes.models import Category, Tag, Note


class NoteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.tag = Tag.objects.create(
            name='testtag',
            user=self.user
        )
        self.note = Note.objects.create(
            title='Test Note',
            content='This is test content',
            category=self.category,
            user=self.user
        )
        self.note.tags.add(self.tag)

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )

    def test_get_notes_authenticated(self):
        """Test retrieving notes list for authenticated user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api-note-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_get_notes_unauthenticated(self):
        """Test that unauthenticated users cannot access API"""
        response = self.client.get(reverse('api-note-list'))
        self.assertTrue(response.status_code in (
            status.HTTP_401_UNAUTHORIZED, 
            status.HTTP_403_FORBIDDEN
        ))

    def test_get_note_detail(self):
        """Test retrieving single note detail"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse('api-note-detail', kwargs={'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_note(self):
        """Test creating a new note via API"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'API Created Note',
            'content': 'This note was created via API',
            'category': self.category.id,
            'tags': [self.tag.id]
        }
        response = self.client.post(reverse('api-note-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify note was created in database
        self.assertTrue(
            Note.objects.filter(title='API Created Note').exists()
        )
        
    def test_update_note(self):
        """Test updating a note via API"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Updated Via API',
            'content': 'This content was updated via API',
            'category': self.category.id
        }
        response = self.client.put(
            reverse('api-note-detail', kwargs={'pk': self.note.pk}),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify note was updated in database
        updated_note = Note.objects.get(pk=self.note.pk)
        self.assertEqual(updated_note.title, 'Updated Via API')
        self.assertEqual(
            updated_note.content, 
            'This content was updated via API'
        )
        
    def test_delete_note(self):
        """Test deleting a note via API"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse('api-note-detail', kwargs={'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify note was deleted from database
        self.assertFalse(
            Note.objects.filter(pk=self.note.pk).exists()
        )
        
    def test_note_api_permissions(self):
        """Test that users cannot access other users' notes via API"""
        self.client.force_authenticate(user=self.other_user)
        
        # Try to get another user's note
        response = self.client.get(
            reverse('api-note-detail', kwargs={'pk': self.note.pk})
        )
        self.assertTrue(response.status_code in (
            status.HTTP_404_NOT_FOUND, 
            status.HTTP_403_FORBIDDEN
        ))
        
        # Try to update another user's note
        data = {'title': 'Should Not Update'}
        response = self.client.put(
            reverse('api-note-detail', kwargs={'pk': self.note.pk}),
            data
        )
        self.assertTrue(response.status_code in (
            status.HTTP_404_NOT_FOUND, 
            status.HTTP_403_FORBIDDEN
        ))
        
        # Try to delete another user's note
        response = self.client.delete(
            reverse('api-note-detail', kwargs={'pk': self.note.pk})
        )
        self.assertTrue(response.status_code in (
            status.HTTP_404_NOT_FOUND, 
            status.HTTP_403_FORBIDDEN
        ))
        
        # Verify note was not deleted
        self.assertTrue(
            Note.objects.filter(pk=self.note.pk).exists()
        )


class CategoryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )

    def test_get_categories(self):
        """Test retrieving categories list"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api-category-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_create_category(self):
        """Test creating a new category via API"""
        self.client.force_authenticate(user=self.user)
        data = {'name': 'API Created Category'}
        response = self.client.post(reverse('api-category-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify category was created in database
        self.assertTrue(
            Category.objects.filter(name='API Created Category').exists()
        )


class TagAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.tag = Tag.objects.create(
            name='testtag',
            user=self.user
        )

    def test_get_tags(self):
        """Test retrieving tags list"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('api-tag-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_create_tag(self):
        """Test creating a new tag via API"""
        self.client.force_authenticate(user=self.user)
        data = {'name': 'newtag'}
        response = self.client.post(reverse('api-tag-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify tag was created in database
        self.assertTrue(
            Tag.objects.filter(name='newtag').exists()
        ) 