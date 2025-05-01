from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('notes/', views.note_list, name='list'),
    path('notes/create/', views.note_create, name='create'),
    path('notes/<int:pk>/', views.note_detail, name='detail'),
    path('notes/<int:pk>/edit/', views.note_edit, name='edit'),
    path('notes/<int:pk>/delete/', views.note_delete, name='delete'),
    path('notes/export/pdf/', views.export_notes, name='export_pdf'),
    path('notes/search/', views.advanced_search, name='advanced_search'),
    
    # New note action URLs
    path('notes/<int:pk>/share/', views.note_share, name='share'),
    path('notes/<int:pk>/share/<int:share_id>/delete/', views.note_share_delete, name='share_delete'),
    path('notes/<int:pk>/attachment/add/', views.note_add_attachment, name='add_attachment'),
    path('notes/<int:pk>/attachment/<int:attachment_id>/delete/', views.note_delete_attachment, name='delete_attachment'),
    
    # Shared notes
    path('notes/shared/', views.shared_notes_list, name='shared_notes'),
    path('notes/shared-by-me/', views.notes_shared_by_me, name='shared_by_me'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Tag URLs
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/', views.tag_detail, name='tag_detail'),
    path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),
    
    # API documentation
    path('api/docs/', views.api_docs, name='api_docs'),
] 