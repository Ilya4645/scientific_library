import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from accounts.models import User


@pytest.mark.django_db
@pytest.mark.view
class TestAccountsViews:
    """Тесты представлений аккаунтов"""

    def test_register_page_status(self, client):
        """Тест статуса страницы регистрации"""
        response = client.get(reverse('accounts:register'))
        assert response.status_code == 200
        assert 'accounts/register.html' in [t.name for t in response.templates]

    def test_login_page_status(self, client):
        """Тест статуса страницы входа"""
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200
        assert 'accounts/login.html' in [t.name for t in response.templates]

    def test_successful_registration(self, client):
        """Тест успешной регистрации"""
        response = client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        })
        assert response.status_code == 302  # Redirect after success
        assert User.objects.filter(username='newuser').exists()

    def test_successful_login(self, client, test_user, test_password):
        """Тест успешного входа"""
        response = client.post(reverse('accounts:login'), {
            'username': test_user.username,
            'password': test_password
        })
        assert response.status_code == 302

    def test_profile_page_requires_login(self, client):
        """Тест: страница профиля требует авторизации"""
        response = client.get(reverse('accounts:profile'))
        assert response.status_code == 302
        assert response.url.startswith('/accounts/login/')

    def test_profile_page_accessible_when_logged_in(self, authenticated_client):
        """Тест: страница профиля доступна авторизованному пользователю"""
        response = authenticated_client.get(reverse('accounts:profile'))
        assert response.status_code == 200
        assert 'accounts/profile.html' in [t.name for t in response.templates]

    def test_become_author_page_authenticated(self, authenticated_client):
        """Тест: страница становления автором доступна авторизованному пользователю"""
        response = authenticated_client.get(reverse('accounts:become_author'))
        assert response.status_code == 200
        assert 'accounts/become_author.html' in [t.name for t in response.templates]

    def test_become_author_post(self, authenticated_client, test_user):
        """Тест: POST запрос на становление автором"""
        response = authenticated_client.post(reverse('accounts:become_author'))

        test_user.refresh_from_db()
        assert test_user.role == 'author'
        assert response.status_code == 302

    def test_top_up_balance_page(self, authenticated_client):
        """Тест: страница пополнения баланса"""
        response = authenticated_client.get(reverse('accounts:top_up_balance'))
        assert response.status_code == 200

    def test_top_up_balance_post(self, authenticated_client, test_user):
        """Тест: POST запрос на пополнение баланса"""
        initial_balance = test_user.profile.balance

        response = authenticated_client.post(reverse('accounts:top_up_balance'), {
            'amount': '100.00'
        })

        test_user.profile.refresh_from_db()
        assert test_user.profile.balance == initial_balance + 100
        assert response.status_code == 302

    def test_logout_functionality(self, authenticated_client):
        """Тест выхода из системы"""
        response = authenticated_client.post(reverse('accounts:logout'))
        assert response.status_code == 302

    def test_author_detail_page_requires_login(self, client, test_author):
        """Тест: страница автора требует авторизации"""
        response = client.get(reverse('accounts:author_detail', args=[test_author.id]))
        assert response.status_code == 302

    def test_author_detail_page_accessible_when_logged_in(self, authenticated_client, test_author):
        """Тест: страница автора доступна авторизованному пользователю"""
        response = authenticated_client.get(reverse('accounts:author_detail', args=[test_author.id]))
        assert response.status_code == 200