from django.urls import path, re_path
from .views import GetAllLinkView, CreateLinkView, BulkCreateLinksView, ExportLinksView, RedirectView, \
    CreatingLinkStatusView, ExportLinksStatusView



urlpatterns = [
    path('get_links/', GetAllLinkView.as_view({'get': 'get'}, name='retrive_links')),
    path('create/', CreateLinkView.as_view({'post': 'post'}), name='create_link'),
    path('bulk-create/status/<str:task_id>', CreatingLinkStatusView.as_view(), name='status-of-link'),
    path('bulk-create/', BulkCreateLinksView.as_view({'post': 'post'}), name='bulk_create_links'),
    path('export/', ExportLinksView.as_view(), name='export_links'),
    path('export/status/<str:task_id>', ExportLinksStatusView.as_view(), name='status-of-export'),
    re_path(r'^(?P<code>[\w\-\u0400-\u04FF]+)/$', RedirectView.as_view(), name='redirect'),
]