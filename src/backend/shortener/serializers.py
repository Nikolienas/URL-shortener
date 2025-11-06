import os
from rest_framework import serializers
from .models import Link, Template
from urllib.parse import unquote

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ('id', 'url_template')

class LinkSerializer(serializers.ModelSerializer):
    is_taken = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Link
        fields = ('id', 'url', 'code', 'description', 'tags', 'created_at', 'template', 'template_fields', 'is_taken')
        read_only_fields = ['code', 'created_at', 'is_active', 'is_taken']

    def create(self, validated_data):
        instance = Link.objects.create(**validated_data)

        template_data = validated_data.pop('template', None)

        if template_data:
            instance.template = template_data

        instance.is_active = True

        instance.save()

        return instance

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

    def get_is_taken(self, obj):
        return obj.is_taken()

class BulkLinkSerializer(serializers.Serializer):
    file = serializers.FileField()

class LinkGETSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    is_taken = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Link
        fields = ('id', 'url', 'code', 'description', 'tags', 'created_at', 'is_active', 'is_taken', 'template', 'template_fields')

    def get_code(self, obj):
        domain_name = os.getenv('DOMAIN_NAME')
        instance = f'{domain_name}/{obj.code}'
        return instance
    
    def get_is_taken(self, obj):
        return obj.is_taken()