from django.urls import path
from .views import GetAllLinkView, CreateLinkView, BulkCreateLinksView, ExportLinksView

urlpatterns = [
    path('get_links/', GetAllLinkView.as_view({'get': 'get'}, name='retrive_links')),
    path('create/', CreateLinkView.as_view({'post': 'post'}), name='create_link'),
    path('bulk-create/', BulkCreateLinksView.as_view({'post': 'post'}), name='bulk_create_links'),
    path('export/', ExportLinksView.as_view(), name='export_links'),
]