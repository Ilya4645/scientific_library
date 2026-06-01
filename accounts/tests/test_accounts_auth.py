import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory, AuthorFactory, ModeratorFactory


@pytest.mark.django_db
class TestAuthorization:
    """Тесты авторизации и доступа"""

    def test_unauthenticated_user_cannot_access_profile(self, client):
        """Неавторизованный пользователь не может зайти в профиль"""
        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 302
        assert response.url.startswith('/accounts/login/')

    def test_authenticated_user_can_access_profile(self, authenticated_client):
        """Авторизованный пользователь может зайти в профиль"""
        response = authenticated_client.get(reverse('accounts:profile'))
        assert response.status_code == 200

    def test_user_can_become_author(self, authenticated_client, test_user):
        """Обычный пользователь может стать автором"""
        response = authenticated_client.post(reverse('accounts:become_author'))
        test_user.refresh_from_db()
        assert test_user.role == 'author'

    def test_author_can_access_work_create(self, author_client):
        """Автор может создавать работы"""
        response = author_client.get(reverse('works:work_create'))
        assert response.status_code == 200

    def test_user_cannot_access_work_create(self, authenticated_client):
        """Обычный пользователь не может создавать работы"""
        response = authenticated_client.get(reverse('works:work_create'))
        assert response.status_code == 403

    def test_moderator_can_access_moderation_queue(self, moderator_client):
        """Модератор может зайти в очередь модерации"""
        response = moderator_client.get(reverse('moderation:queue'))
        assert response.status_code == 200

    def test_user_cannot_access_moderation_queue(self, authenticated_client):
        """Обычный пользователь не может зайти в очередь модерации"""
        response = authenticated_client.get(reverse('moderation:queue'))
        assert response.status_code == 403

    def test_author_cannot_access_moderation_queue(self, author_client):
        """Автор не может зайти в очередь модерации"""
        response = author_client.get(reverse('moderation:queue'))
        assert response.status_code == 403

    @pytest.mark.parametrize('role,url_name,expected_status', [
        ('user', 'works:work_create', 403),
        ('author', 'works:work_create', 200),
        ('moderator', 'works:work_create', 200),
        ('user', 'moderation:queue', 403),
        ('moderator', 'moderation:queue', 200),
        ('admin', 'moderation:queue', 200),
    ])
    def test_role_based_access(self, client, test_password, role, url_name, expected_status):
        """Тест доступа на основе ролей"""
        user = UserFactory(role=role, password='testpass123')
        client.login(username=user.username, password='testpass123')

        response = client.get(reverse(url_name))
        assert response.status_code == expected_status