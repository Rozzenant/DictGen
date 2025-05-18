from django.core.management.base import BaseCommand
from tests.test_data import create_test_data

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **options):
        create_test_data() 