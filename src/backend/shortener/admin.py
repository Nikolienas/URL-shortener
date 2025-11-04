from django.contrib import admin
from .models import Link

class LinkAdmin(admin.ModelAdmin):
    list_display = ("url", 'code', 'tags', 'created_at')

    # list_filter = ('original_url', 'short_code', 'created_at')

admin.site.register(Link, LinkAdmin)