import factory
from factory.django import DjangoModelFactory
from decimal import Decimal
from works.models import Work, Category


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: f'Категория {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')
    description = factory.Faker('text', max_nb_chars=200)
    icon = 'bi-tag'


class WorkFactory(DjangoModelFactory):
    class Meta:
        model = Work

    title = factory.Sequence(lambda n: f'Работа {n}')
    description = factory.Faker('text', max_nb_chars=500)
    price = Decimal('0.00')
    moderation_status = 'pending'
    downloads_count = 0

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for category in extracted:
                self.categories.add(category)


class ApprovedWorkFactory(WorkFactory):
    moderation_status = 'approved'


class PaidWorkFactory(WorkFactory):
    price = Decimal('100.00')
    moderation_status = 'approved'