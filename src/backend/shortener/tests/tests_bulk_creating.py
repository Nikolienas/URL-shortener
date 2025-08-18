import base64
from unittest.mock import patch, MagicMock
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile



@pytest.fixture
def client():
    return APIClient()

def create_xlsx_file(content=b'Test XLSX content'):
    return SimpleUploadedFile('test.xlsx', content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def create_non_xlsx_file():
    return SimpleUploadedFile('test.txt', b'Test text content', content_type='text/plain')

@pytest.mark.django_db
def test_bulk_create_links_invalid_serializer(client):
    response = client.post(reverse('bulk_create_links'), data={}, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'file' in response.data 

@pytest.mark.django_db
def test_bulk_create_links_non_xlsx_file(client):
    file = create_non_xlsx_file()
    response = client.post(reverse('bulk_create_links'), data={'file': file}, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "File must be .xlsx"}

@pytest.mark.django_db
@patch('shortener.tasks.bulk_create_links.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_bulk_create_links_success(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    task.result = {'success': 'Ссылки созданы'}
    mock_task.return_value = task

    mock_time.side_effect = [0, 1, 2, 2, 2, 2, 2]

    file = create_xlsx_file()
    file_content = file.read()
    file.seek(0)
    expected_base64 = base64.b64encode(file_content).decode('utf-8')

    def set_success(*args):
        task.state = 'SUCCESS'

    mock_sleep.side_effect = set_success

    response = client.post(reverse('bulk_create_links'), data={'file': file}, format='multipart')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == {'success': 'Ссылки созданы'}
    mock_task.assert_called_once_with(expected_base64, 'http://testserver/')

@pytest.mark.django_db
@patch('shortener.tasks.bulk_create_links.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_bulk_create_links_task_failure(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    mock_task.return_value = task

    mock_time.side_effect = [0, 1, 2, 2, 2, 2, 2]

    file = create_xlsx_file()
    def set_failure(*args):
        task.state = 'FAILURE'

    mock_sleep.side_effect = set_failure

    response = client.post(reverse('bulk_create_links'), data={'file': file}, format='multipart')
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"error": "Задача не выполнена"}

@pytest.mark.django_db
@patch('shortener.tasks.bulk_create_links.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_bulk_create_links_timeout(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    mock_task.return_value = task

    mock_time.side_effect = [0, 301, 301, 301, 301]

    file = create_xlsx_file()
    mock_sleep.return_value = None

    response = client.post(reverse('bulk_create_links'), data={'file': file}, format='multipart')
    assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert response.data == {"error": "Время задачи истекло"}

@pytest.mark.django_db
@patch('shortener.tasks.bulk_create_links.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_bulk_create_links_task_error_result(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    task.result = {'error': 'Произошла ошибка'}
    mock_task.return_value = task

    mock_time.side_effect = [0, 1, 2, 2, 2, 2, 2]

    file = create_xlsx_file()
    def set_success(*args):
        task.state = 'SUCCESS'

    mock_sleep.side_effect = set_success

    response = client.post(reverse('bulk_create_links'), data={'file': file}, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "Произошла ошибка"}

@pytest.mark.django_db
@patch('shortener.tasks.bulk_create_links.delay')
def test_bulk_create_links_exception(mock_task, client):
    mock_task.side_effect = Exception('Неожиданная ошибка')
    file = create_xlsx_file()
    response = client.post(reverse('bulk_create_links'), data={'file': file}, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "Неожиданная ошибка"}