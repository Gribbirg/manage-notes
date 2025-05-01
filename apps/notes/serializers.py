from rest_framework import serializers
from .models import Note, Category, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['user']


class CategorySerializer(serializers.ModelSerializer):
    note_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'created_at', 'note_count']
        read_only_fields = ['user', 'created_at']
    
    def get_note_count(self, obj):
        return obj.notes.count()


class NoteSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    tags_list = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='tags'
    )
    
    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'category', 'category_name', 
                  'tags', 'tags_list', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    
    def validate_category(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("You don't have access to this category")
        return value
    
    def validate_tags_list(self, value):
        for tag in value:
            if tag.user != self.context['request'].user:
                raise serializers.ValidationError(f"You don't have access to tag: {tag.name}")
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data) 