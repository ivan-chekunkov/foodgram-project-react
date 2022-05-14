from django.core.management import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):

    help = 'Создаем тегов'

    def handle(self, *args, **kwargs):
        data = [
            {'name': 'Завтрак', 'color': '#ADFF2F', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#FF0000', 'slug': 'dinner'},
            {'name': 'Ужин', 'color': '#00BFFF', 'slug': 'supper'}]
        Tag.objects.bulk_create(Tag(**tag) for tag in data)
        self.stdout.write(self.style.SUCCESS('Все тэги загружены!'))
