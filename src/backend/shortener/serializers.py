import os
from rest_framework import serializers
from .models import Link
from urllib.parse import unquote

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('id', 'url', 'code', 'description', 'tags', 'created_at')
        read_only_fields = ['code', 'created_at']

    def validate_tags(self, value):
        """Валидация на раздаление тега через запятую"""
        if value:
            tags = [tag.strip() for tag in value.split(',')]
            if any(not tag for tag in tags):
                raise serializers.ValidationError("Отсвутствует тэг")
            return ','.join(tags)
        return value
    
    def to_representation(self, instance):
        """Декодирует URL при отдаче данных"""
        data = super().to_representation(instance)
        data['url'] = unquote(instance.url)
        return data
    
    def to_internal_value(self, data):
        """Кодирует URL при сохранении"""
        from urllib.parse import quote
        if 'url' in data:
            data['url'] = quote(data['url'], safe=':/?&=')
        return super().to_internal_value(data)

class BulkLinkSerializer(serializers.Serializer):
    file = serializers.FileField()

class LinkGETSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    class Meta:
        model = Link
        fields = ('id', 'url', 'code', 'description', 'tags', 'created_at')

    def code(self, obj):
        domain_name = os.getenv('DOMAIN_NAME')
        instance = f'{domain_name}/{obj.code}'
        return instance