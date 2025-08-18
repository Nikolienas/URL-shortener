from io import BytesIO
import zipfile
import xlsxwriter
from celery import shared_task
from .models import Link  # Замените на вашу модель
import qrcode
from qrcode.image.svg import SvgPathImage
from qrcode.image.pil import PilImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import logging
import base64
from django.core.files.storage import default_storage
from openpyxl import load_workbook
from common.utils.chunk_parsing import get_chunks

logger = logging.getLogger(__name__)

@shared_task
def generate_export_file(base_url, generate_qr=True):
    '''Создание и экспортирование ZIP файла, с Excel SVG|PDF файлами'''
    try:
        # Создание Excel файла
        excel_buffer = BytesIO()
        workbook = xlsxwriter.Workbook(excel_buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        headers = ['url', 'short_url', 'description', 'tags']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        links = Link.objects.all()
        row = 1
        links_data = []
        for chunk in get_chunks(links, chunk_size=1000):
            for link in chunk:
                links_data.append((link.original_url, link.short_code, link.description or '', link.tags or ''))
                worksheet.write(row, 0, link.original_url)
                worksheet.write(row, 1, f"{base_url}{link.short_code}")
                worksheet.write(row, 2, link.description or '')
                worksheet.write(row, 3, link.tags or '')
                row += 1

        workbook.close()
        excel_buffer.seek(0)

        # Создание ZIP файла
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('links.xlsx', excel_buffer.getvalue())

            if generate_qr:
                for _, short_code, _, _ in links_data:
                    short_url = f"{base_url}{short_code}"

                    # Создание SVG QR-кодов
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(short_url)
                    qr.make(fit=True)
                    svg_buffer = BytesIO()
                    qr.make_image(image_factory=SvgPathImage).save(svg_buffer)
                    zip_file.writestr(f"qr_codes/{short_code}.svg", svg_buffer.getvalue())

                    # Создание PDF QR-кодов
                    pdf_buffer = BytesIO()
                    c = canvas.Canvas(pdf_buffer, pagesize=A4)
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(short_url)
                    qr.make(fit=True)
                    img = qr.make_image(image_factory=PilImage)
                    img_buffer = BytesIO()
                    img.save(img_buffer, format="PNG")
                    img_buffer.seek(0)
                    image_reader = ImageReader(img_buffer)
                    c.drawImage(image_reader, 50, 50, width=200, height=200)
                    c.showPage()
                    c.save()
                    zip_file.writestr(f"qr_codes/{short_code}.pdf", pdf_buffer.getvalue())

        zip_buffer.seek(0)
        zip_data = zip_buffer.getvalue()
        return base64.b64encode(zip_data).decode('utf-8')
    except Exception as e:
        return {"error": str(e)}
    
@shared_task
def bulk_create_links(file_content_base64, base_url):
    '''Экспортирование Excel файла в БД'''
    try:
        # Декодирование содержимого файла из base64
        file_content = base64.b64decode(file_content_base64)
        file_buffer = BytesIO(file_content)
        
        # Чтение Excel файла
        workbook = load_workbook(file_buffer, read_only=True)
        sheet = workbook.active
        headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1)) if cell.value]
        required_columns = ['url']
        if not all(col in headers for col in required_columns):
            raise ValueError("В Excel файле должна быть колонка -> url")

        links_to_create = []
        created_links = []
        batch_size = 1000

        for row in sheet.iter_rows(min_row=2, values_only=True):
            url = row[headers.index('url')]
            if isinstance(url, str) and url.startswith('http'):
                link_data = {
                    "original_url": url,
                    "description": row[headers.index('description')] if 'description' in headers and row[headers.index('description')] is not None else '',
                    "tags": row[headers.index('tags')] if 'tags' in headers and row[headers.index('tags')] is not None else ''
                }
                links_to_create.append(Link(**link_data))

            if len(links_to_create) >= batch_size:
                # Создание записей
                Link.objects.bulk_create(links_to_create, batch_size=batch_size)
                for link in links_to_create:
                    short_url = f"{base_url}{link.short_code}"
                    created_links.append({
                        "original_url": link.original_url,
                        "short_url": short_url,
                        "description": link.description,
                        "tags": link.tags
                    })
                links_to_create = []

        # Создание оставшихся записей
        if links_to_create:
            Link.objects.bulk_create(links_to_create, batch_size=batch_size)
            for link in links_to_create:
                short_url = f"{base_url}{link.short_code}"
                created_links.append({
                    "original_url": link.original_url,
                    "short_url": short_url,
                    "description": link.description,
                    "tags": link.tags
                })

        return {"created_links": created_links}
    except Exception as e:
        return {"error": str(e)}