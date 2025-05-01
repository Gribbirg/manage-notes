from django.contrib import admin
from .models import Category, Tag, Note


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    list_filter = ('user',)
    search_fields = ('name',)
    date_hierarchy = 'created_at'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)
    search_fields = ('name',)


class TagInline(admin.TabularInline):
    model = Note.tags.through
    extra = 1


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'get_tags', 'created_at', 'updated_at')
    list_filter = ('user', 'category', 'tags')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)
    fieldsets = (
        (None, {
            'fields': ('title', 'content')
        }),
        ('Classification', {
            'fields': ('category', 'tags')
        }),
        ('Metadata', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
    )
    
    def get_tags(self, obj):
        return obj.get_tags_display()
    
    get_tags.short_description = 'Tags'
