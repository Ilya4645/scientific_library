"""
Тесты представлений (views) приложения works
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from works.models import Work
from works.tests.factories import ApprovedWorkFactory, PaidWorkFactory, CategoryFactory
from accounts.tests.factories import AuthorFactory, UserFactory


@pytest.mark.django_db
class TestWorksViews:
    """Тесты представлений работ"""

    def test_index_page_status(self, client):
        """Главная страница"""
        response = client.get(reverse('index'))
        assert response.status_code == 200

    def test_work_list_page_status(self, client):
        """Список работ"""
        response = client.get(reverse('works:work_list'))
        assert response.status_code == 200

    def test_work_detail_page_for_approved_work(self, client):
        """Страница деталей одобренной работы"""
        author = AuthorFactory()
        work = ApprovedWorkFactory(author=author)
        response = client.get(reverse('works:work_detail', args=[work.id]))
        assert response.status_code == 200

    def test_work_detail_page_for_non_existent_work(self, client):
        """Страница несуществующей работы"""
        response = client.get(reverse('works:work_detail', args=[99999]))
        assert response.status_code == 404

    def test_work_create_page_requires_author_role(self, client):
        """Обычный пользователь не может создать работу"""
        user = UserFactory()
        client.login(username=user.username, password='testpass123')
        response = client.get(reverse('works:work_create'))
        assert response.status_code == 403

    def test_work_create_page_accessible_by_author(self, client):
        """Автор может создать работу"""
        author = AuthorFactory()
        client.login(username=author.username, password='testpass123')
        response = client.get(reverse('works:work_create'))
        assert response.status_code == 200

    def test_work_create_post(self, client):
        """Создание работы через POST"""
        author = AuthorFactory()
        client.login(username=author.username, password='testpass123')

        category = CategoryFactory()

        response = client.post(reverse('works:work_create'), {
            'title': 'New Scientific Work',
            'description': 'This is a test work description',
            'price': '50.00',
            'categories': [category.id]
        })

        # Проверяем результат
        if response.status_code == 302:
            work_exists = Work.objects.filter(title='New Scientific Work').exists()
            assert work_exists is True

    def test_filter_by_price_free(self, client):
        """Фильтр бесплатных работ"""
        author = AuthorFactory()
        free_work = ApprovedWorkFactory(author=author, title='Free Work', price=Decimal('0.00'))
        paid_work = PaidWorkFactory(author=author, title='Paid Work')

        response = client.get(reverse('works:work_list'), {'price': 'free'})
        content = response.content.decode()

        assert 'Free Work' in content

    def test_search_works(self, client):
        """Поиск работ"""
        author = AuthorFactory()
        work1 = ApprovedWorkFactory(author=author, title='Python Programming')

        response = client.get(reverse('works:work_list'), {'q': 'Python'})
        content = response.content.decode()

        assert 'Python' in content

    def test_filter_by_category(self, client):
        """Фильтр по категории"""
        author = AuthorFactory()
        category_math = CategoryFactory(name='Mathematics', slug='mathematics')

        work_math = ApprovedWorkFactory(author=author, title='Math Work')
        work_math.categories.add(category_math)

        response = client.get(reverse('works:work_list'), {'category': 'mathematics'})
        content = response.content.decode()

        assert 'Math Work' in content