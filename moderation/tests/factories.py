import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from decimal import Decimal

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Фабрика для создания пользователей"""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role = 'user'


class AuthorFactory(UserFactory):
    """Фабрика для создания авторов"""
    role = 'author'


class ModeratorFactory(UserFactory):
    """Фабрика для создания модераторов"""
    role = 'moderator'


class UserProfileFactory(DjangoModelFactory):
    """Фабрика для создания профилей пользователей"""

    class Meta:
        model = 'accounts.UserProfile'

    user = factory.SubFactory(UserFactory)
    balance = Decimal('0.00')
    bio = factory.Faker('text', max_nb_chars=200)
    institution = factory.Faker('company')