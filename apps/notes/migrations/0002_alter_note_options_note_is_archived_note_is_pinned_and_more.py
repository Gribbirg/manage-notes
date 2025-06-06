# Generated by Django 5.2 on 2025-05-01 16:44

import apps.notes.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='note',
            options={'ordering': ['-is_pinned', '-updated_at']},
        ),
        migrations.AddField(
            model_name='note',
            name='is_archived',
            field=models.BooleanField(default=False, help_text='Archive this note'),
        ),
        migrations.AddField(
            model_name='note',
            name='is_pinned',
            field=models.BooleanField(default=False, help_text='Pin this note to the top'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, validators=[apps.notes.validators.validate_category_name]),
        ),
        migrations.AlterField(
            model_name='note',
            name='content',
            field=models.TextField(validators=[apps.notes.validators.validate_note_content]),
        ),
        migrations.AlterField(
            model_name='note',
            name='title',
            field=models.CharField(max_length=200, validators=[apps.notes.validators.validate_note_title]),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=50, validators=[apps.notes.validators.validate_tag_name]),
        ),
        migrations.CreateModel(
            name='NoteAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='note_attachments/%Y/%m/%d/')),
                ('file_name', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField(help_text='File size in bytes')),
                ('file_type', models.CharField(max_length=100)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='notes.note')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='NoteSharing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.CharField(choices=[('read', 'Read Only'), ('edit', 'Edit'), ('admin', 'Admin')], default='read', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sharing_permissions', to='notes.note')),
                ('shared_with', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_with_me', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
                'unique_together': {('note', 'shared_with')},
            },
        ),
        migrations.AddField(
            model_name='note',
            name='shared_with',
            field=models.ManyToManyField(related_name='shared_notes', through='notes.NoteSharing', to=settings.AUTH_USER_MODEL),
        ),
    ]
