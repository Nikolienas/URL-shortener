import base64
from unittest.mock import patch, MagicMock
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient



@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
@patch('shortener.tasks.generate_export_file.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_export_links_success_with_qr(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    zip_content = b'Test zip content'
    task.result = base64.b64encode(zip_content).decode('utf-8')
    mock_task.return_value = task

    mock_time.side_effect = [0, 1, 2, 2, 2, 2, 2]

    def set_success(*args):
        task.state = 'SUCCESS'

    mock_sleep.side_effect = set_success

    response = client.get(reverse('export_links'), {'generate_qr': 'true'})
    assert response.status_code == status.HTTP_200_OK
    assert response.content == zip_content
    assert response['Content-Type'] == 'application/zip'
    assert response['Content-Disposition'] == 'attachment; filename="links_export.zip"'
    mock_task.assert_called_once_with('http://testserver/', True)

@pytest.mark.django_db
@patch('shortener.tasks.generate_export_file.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_export_links_success_without_qr(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    zip_content = b'Test zip content'
    task.result = base64.b64encode(zip_content).decode('utf-8')
    mock_task.return_value = task

    mock_time.side_effect = [0, 1, 2, 2, 2, 2, 2]

    def set_success(*args):
        task.state = 'SUCCESS'

    mock_sleep.side_effect = set_success

    response = client.get(reverse('export_links'), {'generate_qr': 'false'})
    assert response.status_code == status.HTTP_200_OK
    assert response.content == zip_content
    assert response['Content-Type'] == 'application/zip'
    assert response['Content-Disposition'] == 'attachment; filename="links_export.zip"'
    mock_task.assert_called_once_with('http://testserver/', False)

@pytest.mark.django_db
@patch('shortener.tasks.generate_export_file.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_export_links_task_failure(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    mock_task.return_value = task

    mock_time.side_effect = [0, 1, 2, 2, 2, 2, 2]

    def set_failure(*args):
        task.state = 'FAILURE'

    mock_sleep.side_effect = set_failure

    response = client.get(reverse('export_links'), {'generate_qr': 'true'})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"error": "Task failed"}

@pytest.mark.django_db
@patch('shortener.tasks.generate_export_file.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_export_links_timeout(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    mock_task.return_value = task

    mock_time.side_effect = [0, 301, 301, 301, 301]

    mock_sleep.return_value = None

    response = client.get(reverse('export_links'), {'generate_qr': 'true'})
    assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert response.data == {"error": "Время задачи вышло"}

@pytest.mark.django_db
@patch('shortener.tasks.generate_export_file.delay')
@patch('shortener.views.time.time')
@patch('shortener.views.time.sleep')
def test_export_links_task_error_result(mock_sleep, mock_time, mock_task, client):
    task = MagicMock()
    task.state = 'PENDING'
    task.result = {'error': 'Произошла ошибка'}
    mock_task.return_value = task

    mock_time.side_effect = [0, 1, 2, 2, 2, 2, 2]

    def set_success(*args):
        task.state = 'SUCCESS'

    mock_sleep.side_effect = set_success

    response = client.get(reverse('export_links'), {'generate_qr': 'true'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "Произошла ошибка"}

@pytest.mark.django_db
@patch('shortener.tasks.generate_export_file.delay')
def test_export_links_exception(mock_task, client):
    mock_task.side_effect = Exception('Неизвестная ошибка')

    response = client.get(reverse('export_links'), {'generate_qr': 'true'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "Неизвестная ошибка"}