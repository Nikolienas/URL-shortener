import os
from rest_framework import serializers
from .models import Link

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ['id', 'original_url', 'short_code', 'description', 'tags', 'created_at']
        read_only_fields = ['short_code', 'created_at']

    def validate_tags(self, value):
        """Валидация на раздаление тега через запятую"""
        if value:
            tags = [tag.strip() for tag in value.split(',')]
            if any(not tag for tag in tags):
                raise serializers.ValidationError("Отсвутствует тэг")
            return ','.join(tags)
        return value

class BulkLinkSerializer(serializers.Serializer):
    file = serializers.FileField()

class LinkGETSerializer(serializers.ModelSerializer):
    short_code = serializers.SerializerMethodField()
    class Meta:
        model = Link
        fields = ('id', 'original_url', 'short_code', 'description', 'tags', 'created_at')

    def get_short_code(self, obj):
        domain_name = os.getenv('DOMAIN_NAME')
        instance = f'{domain_name}/{obj.short_code}'
        return instance