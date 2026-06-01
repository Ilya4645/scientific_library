import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from decimal import Decimal

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role = 'user'

    # НЕ создаем профиль здесь - полагаемся на сигнал


class AuthorFactory(UserFactory):
    role = 'author'


class ModeratorFactory(UserFactory):
    role = 'moderator'


class AdminFactory(UserFactory):
    role = 'admin'
    is_staff = True
    is_superuser = True