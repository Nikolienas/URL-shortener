from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async

class Command(BaseCommand):
    help = 'Запуск телеграм бота'

    def handle(self, *args, **options):
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN,
                  default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()

        @dp.message(CommandStart())
        async def start(message: types.Message):
            print('working')

        async def main():
            await dp.start_polling(bot)

        asyncio.run(main())