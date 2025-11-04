from django.db import models
import re
import random
import string
from urllib.parse import quote, unquote
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from urllib.parse import quote

def generate_short_code(length=6):
    """Генерация уникального кода для основного URL"""
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if not Link.objects.filter(code=code).exists():
            return code
        

class Template(models.Model):
    url_template = models.CharField(max_length=512)

    class Meta:
        verbose_name = 'Шаблон URL'
        verbose_name_plural = 'Шаблоны URL'

class Link(models.Model):
    url = models.URLField(max_length=2048)
    name = models.CharField("Название URl-а", null=True, blank=True)
    code = models.CharField(max_length=50, unique=True, default=generate_short_code)
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    template_fields = models.JSONField("Набор данных для подставления ссылки", null=True, blank=True)
    template = models.ForeignKey('Template', on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return f"{self.code} -> {self.name} -> {self.url}"
    
    def get_encoded_url(self):
        """Функция для возврата правильно закодированных русских символов"""
        return quote(self.url, safe=':/?&=')