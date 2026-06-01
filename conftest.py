import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


@pytest.fixture
def test_password():
    """Тестовый пароль"""
    return 'testpass123'


@pytest.fixture
def test_user(db, test_password):
    """Обычный пользователь"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password=test_password
    )
    return user


@pytest.fixture
def test_author(db, test_password):
    """Автор"""
    user = User.objects.create_user(
        username='testauthor',
        email='author@example.com',
        password=test_password
    )
    user.role = 'author'
    user.save()
    return user


@pytest.fixture
def test_moderator(db, test_password):
    """Модератор"""
    user = User.objects.create_user(
        username='testmoderator',
        email='moderator@example.com',
        password=test_password
    )
    user.role = 'moderator'
    user.save()
    return user


@pytest.fixture
def test_admin(db, test_password):
    """Администратор"""
    user = User.objects.create_superuser(
        username='testadmin',
        email='admin@example.com',
        password=test_password
    )
    return user


@pytest.fixture
def authenticated_client(client, test_user, test_password):
    """Клиент с авторизованным обычным пользователем"""
    client.login(username=test_user.username, password=test_password)
    return client


@pytest.fixture
def author_client(client, test_author, test_password):
    """Клиент с авторизованным автором"""
    client.login(username=test_author.username, password=test_password)
    return client


@pytest.fixture
def moderator_client(client, test_moderator, test_password):
    """Клиент с авторизованным модератором"""
    client.login(username=test_moderator.username, password=test_password)
    return client


@pytest.fixture
def admin_client(client, test_admin, test_password):
    """Клиент с авторизованным администратором"""
    client.login(username=test_admin.username, password=test_password)
    return client


@pytest.fixture
def sample_category(db):
    """Тестовая категория"""
    from works.models import Category
    category, _ = Category.objects.get_or_create(
        name='Тестовая категория',
        slug='test-category',
        defaults={'description': 'Категория для тестов'}
    )
    return category


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Автоматически включает доступ к БД для всех тестов"""
    pass