from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse
from django.views.decorators.http import require_POST
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from datetime import datetime

from .models import Note, Category, Tag, NoteSharing, NoteAttachment
from .forms import NoteForm, CategoryForm, TagForm, NoteSearchForm, NoteSharingForm, NoteAttachmentForm
from apps.accounts.validators import require_role, validate_object_owner, validate_object_permission


@login_required
def dashboard(request):
    """Display user dashboard with statistics."""
    # Get user's notes and categories count
    notes_count = Note.objects.filter(user=request.user).count()
    categories_count = Category.objects.filter(user=request.user).count()
    tags_count = Tag.objects.filter(user=request.user).count()
    
    # Get most used categories
    top_categories = Category.objects.filter(user=request.user) \
                    .annotate(notes_count=Count('notes')) \
                    .order_by('-notes_count')[:5]
    
    # Get most recent notes
    recent_notes = Note.objects.filter(user=request.user) \
                  .order_by('-updated_at')[:5]
    
    context = {
        'notes_count': notes_count,
        'categories_count': categories_count,
        'tags_count': tags_count,
        'top_categories': top_categories,
        'recent_notes': recent_notes,
    }
    return render(request, 'notes/dashboard.html', context)


@login_required
def note_list(request):
    """Display a list of user's notes with advanced search and filter functionality."""
    # Initialize search form
    form = NoteSearchForm(request.GET or None, user=request.user)
    
    # Process search form
    if form.is_valid():
        # Use the centralized search method from the form
        notes = form.get_search_queryset(request.user)
    else:
        # If form is not valid or not submitted, show default view
        notes = Note.objects.filter(user=request.user, is_archived=False).order_by('-is_pinned', '-updated_at')
    
    # Get categories and tags for sidebar
    categories = Category.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    
    # Get counts for UI
    total_notes = Note.objects.filter(user=request.user).count()
    archived_notes = Note.objects.filter(user=request.user, is_archived=True).count()
    active_notes = total_notes - archived_notes
    shared_notes = Note.objects.filter(shared_with=request.user).count()
    
    context = {
        'notes': notes,
        'form': form,
        'categories': categories,
        'tags': tags,
        'total_notes': total_notes,
        'active_notes': active_notes,
        'archived_notes': archived_notes,
        'shared_notes': shared_notes,
    }
    return render(request, 'notes/note_list.html', context)


@login_required
def note_detail(request, pk):
    """Display detailed view of a note."""
    # Try to get the note either owned by the user or shared with them
    try:
        note = Note.objects.get(pk=pk)
        
        # Check if user can view this note
        if not note.can_user_view(request.user):
            messages.error(request, "You don't have permission to view this note.")
            return redirect('notes:list')
        
        # Get note attachments
        attachments = note.attachments.all()
        
        # Check if user can edit this note (for template)
        can_edit = note.can_user_edit(request.user)
        
        # Get sharing settings if user is the owner
        if note.user == request.user:
            shared_users = NoteSharing.objects.filter(note=note)
        else:
            shared_users = None
        
        return render(request, 'notes/note_detail.html', {
            'note': note,
            'attachments': attachments,
            'can_edit': can_edit,
            'shared_users': shared_users,
        })
    
    except Note.DoesNotExist:
        messages.error(request, "Note not found.")
        return redirect('notes:list')


@login_required
def note_create(request):
    """Create a new note."""
    if request.method == 'POST':
        # Extract form data manually
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        category_id = request.POST.get('category', None)
        new_tags = request.POST.get('new_tags', '')
        
        # Debug information
        print(f"POST data: {request.POST}")
        print(f"Title: {title}")
        print(f"Content: {content}")
        print(f"Category ID: {category_id}")
        print(f"New tags: {new_tags}")
        
        try:
            # Create note object directly
            note = Note(
                title=title,
                content=content,
                user=request.user
            )
            
            # Set category if provided
            if category_id and category_id != '':
                try:
                    category = Category.objects.get(id=category_id, user=request.user)
                    note.category = category
                except Category.DoesNotExist:
                    messages.warning(request, "Selected category does not exist.")
            
            # Save the note
            note.save()
            
            # Process new tags if provided
            if new_tags:
                tag_names = [t.strip() for t in new_tags.split(',') if t.strip()]
                for tag_name in tag_names:
                    try:
                        tag, created = Tag.objects.get_or_create(
                            name=tag_name,
                            user=request.user
                        )
                        note.tags.add(tag)
                    except Exception as e:
                        messages.warning(request, f"Could not add tag '{tag_name}': {str(e)}")
            
            messages.success(request, "Note created successfully!")
            return redirect('notes:detail', pk=note.pk)
        except Exception as e:
            messages.error(request, f"Error creating note: {str(e)}")
            print(f"Exception: {str(e)}")
            # Create form with POST data to display validation errors
            form = NoteForm(request.POST, user=request.user)
            form.is_valid()  # Run validation to generate error messages
    else:
        form = NoteForm(user=request.user)
    
    return render(request, 'notes/note_form.html', {
        'form': form,
        'title': 'Create Note',
        'button_text': 'Create',
    })


@login_required
def note_edit(request, pk):
    """Edit an existing note."""
    try:
        note = Note.objects.get(pk=pk)
        
        # Check if user can edit this note
        if not note.can_user_edit(request.user):
            messages.error(request, "You don't have permission to edit this note.")
            return redirect('notes:detail', pk=note.pk)
        
        if request.method == 'POST':
            form = NoteForm(request.POST, instance=note, user=request.user)
            if form.is_valid():
                try:
                    note = form.save()
                    
                    # Display any warnings
                    warnings = form.get_warnings()
                    for field, messages_list in warnings.items():
                        for message in messages_list:
                            messages.warning(request, message)
                    
                    messages.success(request, 'Note updated successfully.')
                    return redirect('notes:detail', pk=note.pk)
                except Exception as e:
                    messages.error(request, f'Error updating note: {str(e)}')
        else:
            form = NoteForm(instance=note, user=request.user)
        
        return render(request, 'notes/note_form.html', {
            'form': form,
            'title': 'Edit Note',
            'button_text': 'Update',
            'note': note,
        })
    
    except Note.DoesNotExist:
        messages.error(request, "Note not found.")
        return redirect('notes:list')


@login_required
def note_delete(request, pk):
    """Delete a note."""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    # Validate ownership
    try:
        validate_object_owner(request.user, note)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('notes:list')
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully.')
        return redirect('notes:list')
    
    return render(request, 'notes/note_confirm_delete.html', {'note': note})


@login_required
def category_list(request):
    """Display a list of user's categories."""
    categories = Category.objects.filter(user=request.user)
    
    # Add note counts to each category
    for category in categories:
        category.note_count = category.notes.count()
    
    return render(request, 'notes/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """Create a new category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                category = form.save(commit=False)
                category.user = request.user
                category.save()
                
                messages.success(request, 'Category created successfully.')
                
                # Redirect back to the referring page if available
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('notes:category_list')
            except Exception as e:
                messages.error(request, f'Error creating category: {str(e)}')
                print(f"Exception creating category: {str(e)}")
        else:
            # Form is not valid, errors will be displayed in the template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Field '{field}': {error}")
            print(f"Form errors: {form.errors}")
    else:
        form = CategoryForm(user=request.user)
    
    return render(request, 'notes/category_form.html', {
        'form': form,
        'title': 'Create Category',
        'button_text': 'Create',
    })


@login_required
def category_edit(request, pk):
    """Edit an existing category."""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    # Validate ownership
    try:
        validate_object_owner(request.user, category)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('notes:category_list')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Category updated successfully.')
                return redirect('notes:category_list')
            except Exception as e:
                messages.error(request, f'Error updating category: {str(e)}')
    else:
        form = CategoryForm(instance=category, user=request.user)
    
    return render(request, 'notes/category_form.html', {
        'form': form,
        'title': 'Edit Category',
        'button_text': 'Update',
        'category': category,
    })


@login_required
def category_delete(request, pk):
    """Delete a category."""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    # Validate ownership
    try:
        validate_object_owner(request.user, category)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('notes:category_list')
    
    if request.method == 'POST':
        # Count notes that will be affected
        affected_notes = category.notes.count()
        
        # Delete the category
        category.delete()
        
        if affected_notes > 0:
            messages.info(request, f'Category deleted. {affected_notes} note(s) were updated.')
        else:
            messages.success(request, 'Category deleted successfully.')
        
        return redirect('notes:category_list')
    
    return render(request, 'notes/category_confirm_delete.html', {'category': category})


@login_required
def category_detail(request, pk):
    """Display notes for a specific category."""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    # Validate ownership
    try:
        validate_object_owner(request.user, category)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('notes:category_list')
    
    notes = Note.objects.filter(category=category, user=request.user)
    
    return render(request, 'notes/category_detail.html', {
        'category': category,
        'notes': notes
    })


@login_required
def tag_list(request):
    """Display a list of user's tags."""
    tags = Tag.objects.filter(user=request.user)
    
    # Add note counts to each tag
    for tag in tags:
        tag.note_count = tag.notes.count()
    
    return render(request, 'notes/tag_list.html', {'tags': tags})


@login_required
def tag_create(request):
    """Create a new tag."""
    if request.method == 'POST':
        form = TagForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                tag = form.save(commit=False)
                tag.user = request.user
                tag.save()
                
                messages.success(request, 'Tag created successfully.')
                
                # Redirect back to the referring page if available
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('notes:tag_list')
            except Exception as e:
                messages.error(request, f'Error creating tag: {str(e)}')
                print(f"Exception creating tag: {str(e)}")
        else:
            # Form is not valid, show errors to the user
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Field '{field}': {error}")
            print(f"Form errors: {form.errors}")
    else:
        form = TagForm(user=request.user)
    
    return render(request, 'notes/tag_form.html', {
        'form': form,
        'title': 'Create Tag',
        'button_text': 'Create',
    })


@login_required
def tag_delete(request, pk):
    """Delete a tag."""
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    
    # Validate ownership
    try:
        validate_object_owner(request.user, tag)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('notes:tag_list')
    
    if request.method == 'POST':
        # Count notes that will be affected
        affected_notes = tag.notes.count()
        
        # Delete the tag
        tag.delete()
        
        if affected_notes > 0:
            messages.info(request, f'Tag deleted. Removed from {affected_notes} note(s).')
        else:
            messages.success(request, 'Tag deleted successfully.')
        
        return redirect('notes:tag_list')
    
    return render(request, 'notes/tag_confirm_delete.html', {'tag': tag})


@login_required
def tag_detail(request, pk):
    """Display notes for a specific tag."""
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    
    # Validate ownership
    try:
        validate_object_owner(request.user, tag)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('notes:tag_list')
    
    notes = Note.objects.filter(tags=tag, user=request.user)
    
    return render(request, 'notes/tag_detail.html', {
        'tag': tag,
        'notes': notes
    })


@login_required
def export_notes(request, format='pdf'):
    """
    Export notes as PDF.
    
    This function generates PDF documents containing notes.
    It can export:
    - A single note (when id parameter is provided in the GET query)
    - Multiple notes based on search/filter criteria
    - All user notes if no filters are applied
    
    Required packages:
    - reportlab: For PDF generation (pip install reportlab)
    
    URL patterns:
    - /notes/export/pdf/ - Export all notes or filtered notes
    - /notes/export/pdf/?id=<note_id> - Export a specific note
    
    Additional query parameters:
    - All parameters supported by the NoteSearchForm for filtering
    """
    # Check if a specific note ID was provided
    note_id = request.GET.get('id')
    if note_id:
        try:
            # Get the specific note (ensure user has access)
            note = Note.objects.get(pk=note_id)
            if note.user == request.user or note.shared_with.filter(id=request.user.id).exists():
                notes = [note]  # Just the one note
            else:
                return HttpResponse('You do not have permission to export this note.', status=403)
        except Note.DoesNotExist:
            return HttpResponse('Note not found.', status=404)
    else:
        # Use the search form to filter notes if any filter is applied
        form = NoteSearchForm(request.GET or None, user=request.user)
        
        if request.GET and form.is_valid():
            notes = form.get_search_queryset(request.user)
        else:
            # Default to all user's notes if no filters applied
            notes = Note.objects.filter(user=request.user)
    
    if format != 'pdf':
        # Unsupported format
        return HttpResponse('Only PDF export is supported.', status=400)
    
    # Ensure we have notes to export
    if not notes.exists():
        return HttpResponse('No notes to export.', status=404)
    
    # Create a buffer for the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document using ReportLab
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title="Notes Export",
        author=request.user.username,
        topMargin=1*cm,
        bottomMargin=1*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.darkblue
    )
    
    subheading_style = ParagraphStyle(
        name='CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        name='Meta',
        parent=styles['Italic'],
        fontSize=9,
        textColor=colors.gray
    )
    
    # Create document elements
    elements = []
    
    # Add title and metadata
    elements.append(Paragraph("Notes Export", title_style))
    
    # Add user info and timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"User: {request.user.username}", meta_style))
    elements.append(Paragraph(f"Exported on: {timestamp}", meta_style))
    elements.append(Spacer(1, 1*cm))
    
    # Add count of exported notes
    notes_count = len(notes)
    if note_id:
        elements.append(Paragraph(f"Exporting 1 note", normal_style))
    else:
        elements.append(Paragraph(f"Exporting {notes_count} notes", normal_style))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Export each note
    for i, note in enumerate(notes):
        # Add separator line except for the first note
        if i > 0:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("_" * 70, normal_style))
            elements.append(Spacer(1, 0.5*cm))
        
        # Note title with ID
        elements.append(Paragraph(f"{note.title} (ID: {note.id})", heading_style))
        
        # Metadata table for better formatting
        meta_data = []
        
        if note.category:
            meta_data.append(["Category", note.category.name])
        
        tags = note.get_tags_display()
        if tags:
            meta_data.append(["Tags", tags])
        
        status = "Normal"
        if note.is_pinned:
            status = "Pinned"
        elif note.is_archived:
            status = "Archived"
        
        meta_data.append(["Status", status])
        meta_data.append(["Created", note.created_at.strftime('%Y-%m-%d %H:%M')])
        meta_data.append(["Updated", note.updated_at.strftime('%Y-%m-%d %H:%M')])
        
        if meta_data:
            # Create a table for metadata
            meta_table = Table(meta_data, colWidths=[100, 300])
            meta_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(meta_table)
        
        # Note content
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("Content:", subheading_style))
        
        # Split content into paragraphs and safely encode
        try:
            content_paragraphs = note.content.split('\n')
            for para in content_paragraphs:
                if para.strip():
                    # Replace any special characters that might cause issues
                    safe_para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(safe_para, normal_style))
                else:
                    elements.append(Spacer(1, 0.2*cm))
        except Exception as e:
            # If there's an error with content formatting, add a placeholder
            elements.append(Paragraph(f"[Content formatting error: {str(e)}]", normal_style))
    
    # Add footer with page numbers
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(A4[0] - 2*cm, 1*cm, text)
        canvas.restoreState()
    
    # Build PDF
    try:
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    except Exception as e:
        return HttpResponse(f'Error generating PDF: {str(e)}', status=500)
    
    # Get the value of the buffer and create response
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create filename based on what we're exporting
    if note_id:
        filename = f"note_{note_id}.pdf"
    else:
        if notes_count == 1:
            filename = f"note_{notes[0].id}.pdf"
        else:
            filename = f"notes_export_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Create response with PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# Admin-only views
@login_required
@require_role('admin')
def api_docs(request):
    """Display API documentation."""
    return render(request, 'notes/api_docs.html')


# New views for sharing notes
@login_required
def note_share(request, pk):
    """Share a note with another user."""
    try:
        note = Note.objects.get(pk=pk)
        
        # Only the owner can share a note
        if note.user != request.user:
            messages.error(request, "You don't have permission to share this note.")
            return redirect('notes:detail', pk=note.pk)
        
        if request.method == 'POST':
            form = NoteSharingForm(request.POST, note=note, user=request.user)
            if form.is_valid():
                try:
                    sharing = form.save()
                    messages.success(request, f'Note shared successfully with {sharing.shared_with.username}.')
                    return redirect('notes:detail', pk=note.pk)
                except Exception as e:
                    messages.error(request, f'Error sharing note: {str(e)}')
        else:
            form = NoteSharingForm(note=note, user=request.user)
        
        # Get current sharing settings
        shared_users = NoteSharing.objects.filter(note=note)
        
        return render(request, 'notes/note_share.html', {
            'form': form,
            'note': note,
            'shared_users': shared_users,
        })
    
    except Note.DoesNotExist:
        messages.error(request, "Note not found.")
        return redirect('notes:list')


@login_required
@require_POST
def note_share_delete(request, pk, share_id):
    """Remove sharing for a note."""
    try:
        sharing = NoteSharing.objects.get(id=share_id, note_id=pk)
        
        # Only the owner can change sharing settings
        if sharing.note.user != request.user:
            messages.error(request, "You don't have permission to change sharing settings.")
            return redirect('notes:detail', pk=pk)
        
        username = sharing.shared_with.username
        sharing.delete()
        
        messages.success(request, f'Note is no longer shared with {username}.')
        return redirect('notes:detail', pk=pk)
    
    except NoteSharing.DoesNotExist:
        messages.error(request, "Sharing not found.")
        return redirect('notes:detail', pk=pk)


@login_required
def note_add_attachment(request, pk):
    """Add an attachment to a note."""
    try:
        note = Note.objects.get(pk=pk)
        
        # Check if user can edit this note
        if not note.can_user_edit(request.user):
            messages.error(request, "You don't have permission to add attachments to this note.")
            return redirect('notes:detail', pk=note.pk)
        
        if request.method == 'POST':
            form = NoteAttachmentForm(request.POST, request.FILES, note=note)
            if form.is_valid():
                try:
                    attachment = form.save()
                    messages.success(request, f'Attachment "{attachment.file_name}" added successfully.')
                    return redirect('notes:detail', pk=note.pk)
                except Exception as e:
                    messages.error(request, f'Error adding attachment: {str(e)}')
        else:
            form = NoteAttachmentForm(note=note)
        
        return render(request, 'notes/attachment_form.html', {
            'form': form,
            'note': note,
        })
    
    except Note.DoesNotExist:
        messages.error(request, "Note not found.")
        return redirect('notes:list')


@login_required
@require_POST
def note_delete_attachment(request, pk, attachment_id):
    """Delete an attachment from a note."""
    try:
        attachment = NoteAttachment.objects.get(id=attachment_id, note_id=pk)
        note = attachment.note
        
        # Check if user can edit this note
        if not note.can_user_edit(request.user):
            messages.error(request, "You don't have permission to delete attachments from this note.")
            return redirect('notes:detail', pk=pk)
        
        file_name = attachment.file_name
        attachment.delete()
        
        messages.success(request, f'Attachment "{file_name}" deleted successfully.')
        return redirect('notes:detail', pk=pk)
    
    except NoteAttachment.DoesNotExist:
        messages.error(request, "Attachment not found.")
        return redirect('notes:detail', pk=pk)


@login_required
def shared_notes_list(request):
    """Display a list of notes shared with the user."""
    notes = Note.objects.filter(shared_with=request.user)
    
    return render(request, 'notes/shared_notes_list.html', {
        'notes': notes,
        'title': 'Notes Shared With Me',
    })


@login_required
def notes_shared_by_me(request):
    """Display a list of notes the user has shared with others."""
    # Get distinct notes that the user has shared with others
    shared_note_ids = NoteSharing.objects.filter(note__user=request.user).values_list('note_id', flat=True).distinct()
    notes = Note.objects.filter(id__in=shared_note_ids)
    
    # For each note, add a list of users it's shared with
    for note in notes:
        note.shared_with_users = NoteSharing.objects.filter(note=note)
    
    return render(request, 'notes/notes_shared_by_me.html', {
        'notes': notes,
        'title': 'Notes I\'ve Shared',
    })


@login_required
def advanced_search(request):
    """Display advanced search page with comprehensive filtering options."""
    # Initialize search form
    form = NoteSearchForm(request.GET or None, user=request.user)
    
    # Only process search if the form was submitted
    notes = []
    if request.GET and form.is_valid():
        notes = form.get_search_queryset(request.user)
    
    # Get categories and tags for the form
    categories = Category.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)
    
    # Get some stats for displaying on the page
    notes_count = len(notes) if notes else 0
    
    context = {
        'form': form,
        'notes': notes,
        'notes_count': notes_count,
        'categories': categories,
        'tags': tags,
        'is_search_results': bool(request.GET),
    }
    return render(request, 'notes/advanced_search.html', context)
