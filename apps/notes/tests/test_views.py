from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from apps.notes.models import Category, Tag, Note


class NoteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
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

        # Create another user for permission tests
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )

    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated user"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('notes:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/dashboard.html')
        self.assertContains(response, 'Test Note')

    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view redirects for unauthenticated user"""
        response = self.client.get(reverse('notes:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_note_list_view(self):
        """Test note list view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_list.html')
        self.assertContains(response, 'Test Note')
        
    def test_note_detail_view(self):
        """Test note detail view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            reverse('notes:detail', kwargs={'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_detail.html')
        self.assertContains(response, 'Test Note')
        self.assertContains(response, 'This is test content')
        
    def test_note_create_view(self):
        """Test note create view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('notes:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_form.html')
        
        # Test POST request to create note
        response = self.client.post(
            reverse('notes:create'),
            {
                'title': 'New Test Note',
                'content': 'This is new test content',
                'category': self.category.id,
                'tags': [self.tag.id],
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirects after creation
        
        # Verify note was created
        self.assertTrue(
            Note.objects.filter(title='New Test Note').exists()
        )
        
    def test_note_edit_view(self):
        """Test note edit view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            reverse('notes:edit', kwargs={'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_form.html')
        
        # Test POST request to update note
        response = self.client.post(
            reverse('notes:edit', kwargs={'pk': self.note.pk}),
            {
                'title': 'Updated Note Title',
                'content': 'This is updated content',
                'category': self.category.id,
                'tags': [self.tag.id],
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirects after update
        
        # Verify note was updated
        updated_note = Note.objects.get(pk=self.note.pk)
        self.assertEqual(updated_note.title, 'Updated Note Title')
        self.assertEqual(updated_note.content, 'This is updated content')
        
    def test_note_delete_view(self):
        """Test note delete view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            reverse('notes:delete', kwargs={'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/note_confirm_delete.html')
        
        # Test POST request to delete note
        response = self.client.post(
            reverse('notes:delete', kwargs={'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 302)  # Redirects after delete
        
        # Verify note was deleted
        self.assertFalse(
            Note.objects.filter(pk=self.note.pk).exists()
        )


class CategoryViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )

    def test_category_list_view(self):
        """Test category list view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('notes:category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/category_list.html')
        self.assertContains(response, 'Test Category')
        
    def test_category_detail_view(self):
        """Test category detail view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            reverse('notes:category_detail', kwargs={'pk': self.category.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/category_detail.html')
        self.assertContains(response, 'Test Category')
        
    def test_category_create_view(self):
        """Test category create view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('notes:category_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/category_form.html')
        
        # Test POST request to create category
        response = self.client.post(
            reverse('notes:category_create'),
            {'name': 'New Category'}
        )
        self.assertEqual(response.status_code, 302)  # Redirects after creation
        
        # Verify category was created
        self.assertTrue(
            Category.objects.filter(name='New Category').exists()
        )


class TagViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.tag = Tag.objects.create(
            name='testtag',
            user=self.user
        )

    def test_tag_list_view(self):
        """Test tag list view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('notes:tag_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/tag_list.html')
        self.assertContains(response, 'testtag')
        
    def test_tag_detail_view(self):
        """Test tag detail view"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            reverse('notes:tag_detail', kwargs={'pk': self.tag.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/tag_detail.html')
        self.assertContains(response, 'testtag') 