from django.db import models
import random
import string

def generate_short_code(length=6):
    """Генерация уникального кода для основного URL"""
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if not Link.objects.filter(short_code=code).exists():
            return code

class Link(models.Model):
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=10, unique=True, default=generate_short_code)
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"