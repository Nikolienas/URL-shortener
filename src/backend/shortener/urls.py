from django.urls import path, re_path
from .views import GetAllLinkView, CreateLinkView, BulkCreateLinksView, ExportLinksView, RedirectView, \
    BulkCreateLinkStatusView, ExportLinksStatusView, ExportTemplateView, BulkCreateTemplateView



urlpatterns = [
    path('get_links/', GetAllLinkView.as_view({'get': 'get'}, name='retrive-links')),
    path('create/', CreateLinkView.as_view({'post': 'post'}), name='create-link'),
    path('bulk-create/', BulkCreateLinksView.as_view({'post': 'post'}), name='bulk_create_links'),
    path('bulk-create/status/<str:task_id>', BulkCreateLinkStatusView.as_view(), name='status-of-link'),
    path('bulk_create_template/', BulkCreateTemplateView.as_view(), name='bulk-create-template'),
    path('export/', ExportLinksView.as_view(), name='export_links'),
    path('export/status/<str:task_id>', ExportLinksStatusView.as_view(), name='status-of-export'),
    path('export_template/', ExportTemplateView.as_view(), name='export-template'),
    re_path(r'^(?P<code>[\w\-\u0400-\u04FF]+)/$', RedirectView.as_view(), name='redirect'),
]