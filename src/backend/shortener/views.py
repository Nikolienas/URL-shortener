import os
import base64
import uuid
from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework import viewsets
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from .models import Link
from .serializers import LinkSerializer, BulkLinkSerializer, LinkGETSerializer
from .tasks import generate_export_file, bulk_create_links


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
            short_url = request.build_absolute_uri(f"/{link.code}")
            response_data = {
                "code": short_url,
                "url": link.url,
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

            task_id = str(uuid.uuid4())

            # Чтение содержимого файла и декодирование в base64
            file_content = file.read()
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')

            # Запуск задачу Celery
            task = bulk_create_links.apply_async(
                args=[file_content_base64, request.build_absolute_uri('/')],
                task_id=task_id
            )

            return Response({
                "task_id": task_id,
                "status": "Задача запущена",
                "message": "Экспортирование в БД началась"
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BulkCreateLinkStatusView(APIView):
    def get(self, request, task_id):
        try:
            task = AsyncResult(task_id)
            
            response_data = {
                "task_id": task_id,
                "status": task.status,
            }

            if task.status == 'PENDING':
                response_data.update({
                    "message": "Задача ожидает выполнения или не найдена"
                })
            elif task.status == 'PROGRESS':
                response_data.update({
                    "progress": task.result.get('current', 0),
                    "total": task.result.get('total', 0),
                    "percent": task.result.get('percent', 0),
                    "stage": task.result.get('stage', 'Processing')
                })
            elif task.status == 'SUCCESS':
                response_data["result"] = task.result
            elif task.status == 'FAILURE':
                response_data["error"] = str(task.result)

            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
class ExportLinksView(APIView):
    def get(self, request):
        """Запуск задачи экспорта ссылок"""
        try:
            generate_qr = request.query_params.get('generate_qr', 'true').lower() == 'true'
            
            # Асинхронный запуск задачи
            task = generate_export_file.delay(
                base_url=request.build_absolute_uri('/'),
                generate_qr=generate_qr
            )
            
            return Response({
                "task_id": task.id,
                "status": "Задача запущена",
                "message": "Подготовка файла началась",
                "check_status_url": f"/api/shortener/export/status/{task.id}/"
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExportLinksStatusView(APIView):
    def get(self, request, task_id):
        try:
            task = AsyncResult(task_id)
            
            if task.state == 'PENDING':
                return Response({
                    "status": "В обработке",
                    "state": task.state,
                    "message": "Задача ожидает выполнения"
                }, status=status.HTTP_202_ACCEPTED)
                
            elif task.state == 'PROGRESS':
                progress_data = task.result if task.result else {}
                return Response({
                    "status": "Выполняется",
                    "state": task.state,
                    "progress": progress_data.get('current', 0),
                    "total": progress_data.get('total', 100),
                    "status_message": progress_data.get('status', '')
                }, status=status.HTTP_202_ACCEPTED)
                
            elif task.state == 'SUCCESS':
                result = task.result
                
                if isinstance(result, dict) and "error" in result:
                    return Response(
                        {"error": result["error"]}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if isinstance(result, dict) and "file_path" in result:
                    filepath = result["file_path"]
                    filename = result.get("filename", "links_export.zip")
                    
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            zip_data = f.read()
                        
                        response = HttpResponse(zip_data, content_type='application/zip')
                        response['Content-Disposition'] = f'attachment; filename="{filename}"'
                        response['Content-Length'] = len(zip_data)
                        
                        # Очистка файла после отправки (TODO надо протестировать)
                        # self.cleanup_file(filepath)
                        
                        return response
                    else:
                        return Response({
                            "error": "Файл не найден на сервере",
                            "file_path": filepath
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    return Response({
                        "error": "Неожиданный формат результата задачи",
                        "result_type": type(result).__name__
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            elif task.state == 'FAILURE':
                error_message = "Произошла ошибка при генерации файла"
                if task.result and isinstance(task.result, str):
                    error_message = task.result
                elif task.result and isinstance(task.result, dict) and 'error' in task.result:
                    error_message = task.result['error']
                    
                return Response({
                    "error": error_message,
                    "state": task.state
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            else:
                return Response({
                    "status": "Неизвестный статус",
                    "state": task.state,
                    "result": str(task.result) if task.result else None
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class RedirectView(View):
    def get(self, request, code):
        link = get_object_or_404(Link, code=code)
        return HttpResponseRedirect(link.url)
    
class ExportTemplateView(TemplateView):
    template_name = 'export_template.html'

class BulkCreateTemplateView(TemplateView):
    template_name = 'bulk_create_template.html'