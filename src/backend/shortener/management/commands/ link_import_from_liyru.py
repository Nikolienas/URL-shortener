import json
import logging
import multiprocessing
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand
from tqdm import tqdm

from shortener.enums import Status
from shortener.models import Link, Template


class Command(BaseCommand):

    def __init__(self):
        super().__init__()
        self.template_data = {
            1: {
                'title':    'SPN токен гиперссылка и далее',
                'url':      'https://spnavigator.ru/t/{токен}?next={гиперссылка}%3F{параметры}',
                "created":  "2019-11-19 10:43:00.216633",
                "modified": "2019-11-19 10:43:00.217427",

            },
            2: {
                'title':    'SPN токен гиперссылка источник',
                'url':      'https://spnavigator.ru/t/{токен}?next={гиперссылка}?src={источник}',
                "created":  "2019-11-19 11:51:28.010442",
                "modified": "2019-11-19 11:51:28.010525",

            },
            3: {
                'uid':      '13d55d0f-0dc4-4021-b219-b22fe20a7cc9',
                'title':    '_url_',
                'url':      '{гиперссылка}',
                "created":  "2019-11-19 11:51:37.258250",
                "modified": "2019-11-19 11:51:37.258324",

            },
            4: {
                'title':    '_Универсальный с почтой_',
                'url':      'https://spnavigator.ru/utils/r/{проект}-{код рассылки}/{email}/{гиперссылка}',
                "created":  "2019-12-12 12:15:33.406498",
                "modified": "2019-12-12 12:15:37.875786",

            },
            5: {
                'title':    '_Универсальный с телефоном_',
                'url':      'https://spnavigator.ru/utils/r/{проект}-{код рассылки}/{телефон}/{гиперссылка}',
                "created":  "2019-12-27 21:09:59.796523",
                "modified": "2019-12-27 21:13:20.002874",

            },
        }
        self.excel_dct = {}

    upload_dir: Path
    logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        self.upload_dir = settings.ROOT_DIR / 'upload'
        self.prepare_templates()
        self.prepare_excel_json()
        with (self.upload_dir / 'shorter_link.json').open('r', encoding='utf8') as f:
            data = json.load(f)
        self.link_query(data)

    def prepare_excel_json(self):
        """
        Добавьте dump таблицы excelfile в текушую папку
        и назовите ее shorter_excelfile.json
        """
        with (self.upload_dir / 'shorter_excelfile.json').open('r', encoding='utf8') as file:
            excel_data = json.load(file)
            for excel in excel_data:
                self.excel_dct[excel['id']] = excel

    templates: dict[int, Template] = {}

    def prepare_templates(self):
        """
        Подготовка шаблонов
        """
        for id, template_data in self.template_data.items():
            params = {
                'name':         template_data['title'],
                'url_template': template_data['url'],
                'created':      template_data['created'],
                'modified':     template_data['modified'],
            }
            if 'uid' in template_data:
                params['uid'] = template_data['uid']
            if Template.objects.filter(url_template=params['url_template']).exists():
                template = Template.objects.get(url_template=params['url_template'])
            else:
                template = Template.objects.create(**params)
            self.templates[id] = template

    def link_query(self, data):
        for link in tqdm(data, desc='Загрузка Ссылок'):
            template = self.templates[link['template_id']]
            if link['excel_file_id'] is not None:
                params = {
                    'source_file': self.excel_dct[link['excel_file_id']]['upload_file'],
                    'status':      Status.FINISHED,
                    'template':    template
                }
            #     excel, _ = ExcelFile.objects.get_or_create(**params)
            else:
                excel = None
            params = {
                'code':            link['code'],
                'url':             link['url'],
                'template_fields': link['template_fields'],
                'template':        template,
                # 'excel':           excel,
            }
            if 'created' in link:
                params['created'] = link['created']
            if 'modified' in link:
                params['modified'] = link['modified']
            link = Link.objects.create(**params)
        #     # self.logger.info(f'Create link - {link.code}')
        #     # QRLink.objects.create(link=link)
        #     # self.logger.info(f'Create QR - {link.short_url}')
        assert Link.objects.count() == len(data)
