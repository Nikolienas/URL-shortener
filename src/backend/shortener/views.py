from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from .models import Link
from .serializers import LinkSerializer, BulkLinkSerializer, LinkGETSerializer
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework import viewsets
from .tasks import generate_export_file, bulk_create_links
import time
import base64



class GetAllLinkView(viewsets.ModelViewSet):
    serializer_class = LinkGETSerializer
    def get(self, request):
        instance = Link.objects.all()
        serializer = self.get_serializer(instance, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateLinkView(viewsets.ModelViewSet):
    serializer_class = LinkSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            link = serializer.save()
            short_url = request.build_absolute_uri(f"/{link.short_code}")
            response_data = {
                "short_url": short_url,
                "original_url": link.original_url,
                "description": link.description,
                "tags": link.tags
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkCreateLinksView(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser]
    serializer_class = BulkLinkSerializer

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            file = request.FILES['file']
            if not file.name.endswith('.xlsx'):
                return Response({"error": "File must be .xlsx"}, status=status.HTTP_400_BAD_REQUEST)

            # Чтение содержимого файла и декодирование в base64
            file_content = file.read()
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

            # Запуск задачу Celery
            task = bulk_create_links.delay(file_content_base64, request.build_absolute_uri('/'))

            timeout = 300
            start_time = time.time()
            while True:

                if time.time() - start_time > timeout:
                    return Response({"error": "Время задачи истекло"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                
                if task.state == 'SUCCESS':
                    result = task.result
                    if isinstance(result, dict) and "error" in result:
                        return Response({"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST)
                    return Response(result, status=status.HTTP_201_CREATED)
                
                elif task.state == 'FAILURE':
                    return Response({"error": "Задача не выполнена"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                time.sleep(5)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExportLinksView(APIView):
    def get(self, request):
        try:
            # Запуск задачу Celery
            generate_qr = request.query_params.get('generate_qr', 'true').lower() == 'true'
            task = generate_export_file.delay(request.build_absolute_uri('/'), generate_qr)

            timeout = 300
            start_time = time.time()
            while True:

                if time.time() - start_time > timeout:
                    return Response({"error": "Время задачи вышло"}, status=status.HTTP_504_GATEWAY_TIMEOUT)
                
                if task.state == 'SUCCESS':
                    result = task.result
                    if isinstance(result, dict) and "error" in result:
                        return Response({"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST)
                    zip_data = base64.b64decode(result)
                    response = HttpResponse(zip_data, content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename="links_export.zip"'
                    return response
                
                elif task.state == 'FAILURE':
                    return Response({"error": "Task failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                time.sleep(5)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class RedirectView(View):
    def get(self, request, short_code):
        link = get_object_or_404(Link, short_code=short_code)
        return HttpResponseRedirect(link.original_url)