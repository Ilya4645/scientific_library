"""
Тесты моделей приложения works
"""

import pytest
from django.core.exceptions import ValidationError
from decimal import Decimal  # <---- ВАЖНО! ДОЛЖЕН БЫТЬ ЭТОТ ИМПОРТ
from django.urls import reverse
from works.models import Work, Purchase
from works.tests.factories import WorkFactory, ApprovedWorkFactory, PaidWorkFactory, CategoryFactory
from accounts.tests.factories import AuthorFactory, UserFactory


# ============================================================================
# ТЕСТЫ МОДЕЛИ WORK (НАУЧНАЯ РАБОТА)
# ============================================================================

@pytest.mark.django_db
class TestWorkModel:
    """Тесты модели Work"""

    def test_create_work(self):
        """Создание работы"""
        author = AuthorFactory()
        work = WorkFactory(author=author)

        assert work.title is not None
        assert work.author == author
        assert work.moderation_status == 'pending'
        assert work.downloads_count == 0

    def test_work_str_method(self):
        """Метод __str__"""
        author = AuthorFactory(username='testauthor')
        work = WorkFactory(author=author, title='Test Work')
        expected = f"Test Work - testauthor"

        assert str(work) == expected

    def test_work_validation_negative_price(self):
        """Валидация отрицательной цены"""
        author = AuthorFactory()
        work = WorkFactory.build(author=author, title='Valid Title', price=Decimal('-10.00'))

        with pytest.raises(ValidationError):
            work.clean()

    def test_work_validation_title_too_short(self):
        """Валидация короткого названия"""
        author = AuthorFactory()
        work = WorkFactory.build(author=author, title='Abc')

        with pytest.raises(ValidationError):
            work.clean()

    def test_is_free_method(self):
        """Метод is_free()"""
        author = AuthorFactory()
        free_work = WorkFactory(author=author, price=Decimal('0.00'))
        paid_work = WorkFactory(author=author, price=Decimal('50.00'))

        assert free_work.is_free() is True
        assert paid_work.is_free() is False

    def test_work_with_categories(self):
        """Связь с категориями"""
        author = AuthorFactory()
        category = CategoryFactory()
        work = WorkFactory(author=author)
        work.categories.add(category)

        assert work.categories.count() == 1
        assert work.categories.first().name == category.name

    def test_can_download_free_work_for_any_user(self):
        """Доступ к бесплатной работе"""
        author = AuthorFactory()
        user = UserFactory()
        free_work = ApprovedWorkFactory(author=author, price=Decimal('0.00'))

        assert free_work.can_download(user) is True

    def test_can_download_paid_work_only_after_purchase(self):
        """Доступ к платной работе - только после покупки"""
        author = AuthorFactory()
        user = UserFactory()

        user.refresh_from_db()
        user.profile.balance = Decimal('200.00')
        user.profile.save()

        paid_work = PaidWorkFactory(author=author)

        # ДО ПОКУПКИ
        assert paid_work.can_download(user) is False

        # Создаем покупку
        Purchase.objects.create(
            user=user,
            work=paid_work,
            amount=Decimal(str(paid_work.price))
        )

        # ПОСЛЕ ПОКУПКИ
        assert paid_work.can_download(user) is True


# ============================================================================
# ТЕСТЫ МОДЕЛИ PURCHASE
# ============================================================================

@pytest.mark.django_db
class TestPurchaseModel:
    """Тесты модели Purchase"""

    def test_create_purchase(self):
        """Создание покупки"""
        author = AuthorFactory()
        user = UserFactory()

        user.refresh_from_db()
        user.profile.balance = Decimal('200.00')
        user.profile.save()

        work = PaidWorkFactory(author=author)

        purchase = Purchase.objects.create(
            user=user,
            work=work,
            amount=Decimal(str(work.price))
        )

        assert purchase.user == user
        assert purchase.work == work
        assert purchase.commission == Decimal('10.00')
        assert purchase.author_share == Decimal('90.00')

    def test_purchase_str_method(self):
        """Строковое представление покупки"""
        author = AuthorFactory()
        user = UserFactory()

        user.refresh_from_db()
        user.profile.balance = Decimal('200.00')
        user.profile.save()

        work = PaidWorkFactory(author=author, title='Test Work')

        purchase = Purchase.objects.create(
            user=user,
            work=work,
            amount=Decimal(str(work.price))
        )

        expected = f"{user.username} купил Test Work"
        assert str(purchase) == expected

    def test_purchase_deducts_from_buyer(self):
        """Списание средств с покупателя"""
        author = AuthorFactory()
        user = UserFactory()
        user.refresh_from_db()

        initial_balance = Decimal('200.00')
        user.profile.balance = initial_balance
        user.profile.save()

        work = PaidWorkFactory(author=author)

        Purchase.objects.create(
            user=user,
            work=work,
            amount=Decimal(str(work.price))
        )

        user.refresh_from_db()
        expected = initial_balance - work.price
        assert user.profile.balance == expected

    def test_purchase_adds_to_author(self):
        """Начисление средств автору"""
        author = AuthorFactory()
        author.refresh_from_db()

        initial_author_balance = Decimal('0.00')
        author.profile.balance = initial_author_balance
        author.profile.save()

        user = UserFactory()
        user.refresh_from_db()
        user.profile.balance = Decimal('200.00')
        user.profile.save()

        work = PaidWorkFactory(author=author)

        Purchase.objects.create(
            user=user,
            work=work,
            amount=Decimal(str(work.price))
        )

        author.refresh_from_db()
        expected = initial_author_balance + Decimal('90.00')
        assert author.profile.balance == expected

    def test_purchase_validation_insufficient_funds(self):
        """Валидация при недостатке средств"""
        author = AuthorFactory()
        user = UserFactory()
        user.refresh_from_db()

        user.profile.balance = Decimal('50.00')
        user.profile.save()

        work = PaidWorkFactory(author=author)

        with pytest.raises(ValidationError) as exc_info:
            purchase = Purchase(
                user=user,
                work=work,
                amount=Decimal(str(work.price))
            )
            purchase.clean()
            purchase.save()

        assert "Недостаточно средств" in str(exc_info.value)

    def test_purchase_validation_author_cannot_buy_own_work(self):
        """Валидация - автор не может купить свою работу"""
        author = AuthorFactory()
        author.refresh_from_db()
        author.profile.balance = Decimal('200.00')
        author.profile.save()

        work = PaidWorkFactory(author=author)

        with pytest.raises(ValidationError) as exc_info:
            purchase = Purchase(
                user=author,
                work=work,
                amount=Decimal(str(work.price))
            )
            purchase.clean()

        assert "Автор не может купить свою работу" in str(exc_info.value)

    def test_unique_purchase_constraint(self):
        """Уникальность покупки - нельзя купить дважды"""
        author = AuthorFactory()
        user = UserFactory()
        user.refresh_from_db()
        user.profile.balance = Decimal('200.00')
        user.profile.save()

        work = PaidWorkFactory(author=author)

        # Первая покупка
        Purchase.objects.create(
            user=user,
            work=work,
            amount=Decimal(str(work.price))
        )

        # Вторая покупка - должна вызвать ошибку
        with pytest.raises(Exception):
            Purchase.objects.create(
                user=user,
                work=work,
                amount=Decimal(str(work.price))
            )


# ============================================================================
# ТЕСТЫ ПРОЦЕССА ПОКУПКИ (ЧЕРЕЗ VIEW)
# ============================================================================

@pytest.mark.django_db
class TestPurchaseFlow:
    """Тесты процесса покупки через views"""

    def test_purchase_work_successful(self, client):
        """Успешная покупка работы"""
        author = AuthorFactory()
        user = UserFactory()

        user.refresh_from_db()
        user.profile.balance = Decimal('200.00')
        user.profile.save()

        work = PaidWorkFactory(author=author)

        client.login(username=user.username, password='testpass123')
        response = client.post(reverse('works:purchase_work', args=[work.id]))

        # Проверяем редирект
        assert response.status_code == 302, f"Ожидался редирект 302, получен {response.status_code}"

        # Проверяем создание покупки
        purchase_exists = Purchase.objects.filter(user=user, work=work).exists()
        assert purchase_exists is True, "Покупка должна быть создана"

    def test_purchase_work_insufficient_balance(self, client):
        """Покупка при недостатке средств"""
        author = AuthorFactory()
        user = UserFactory()

        user.refresh_from_db()
        user.profile.balance = Decimal('50.00')
        user.profile.save()

        work = PaidWorkFactory(author=author)

        client.login(username=user.username, password='testpass123')
        response = client.post(reverse('works:purchase_work', args=[work.id]))

        # Должен быть редирект на страницу пополнения баланса
        assert response.status_code == 302, f"Ожидался редирект 302, получен {response.status_code}"

        # Покупка не должна создаться
        purchase_exists = Purchase.objects.filter(user=user, work=work).exists()
        assert purchase_exists is False, "При недостатке средств покупка не должна создаваться"

    def test_cannot_purchase_own_work(self, client):
        """Нельзя купить свою работу"""
        author = AuthorFactory()

        author.refresh_from_db()
        author.profile.balance = Decimal('200.00')
        author.profile.save()

        work = PaidWorkFactory(author=author)

        client.login(username=author.username, password='testpass123')
        response = client.post(reverse('works:purchase_work', args=[work.id]))

        # Должен быть редирект
        assert response.status_code == 302, f"Ожидался редирект 302, получен {response.status_code}"

        # Покупка не должна создаться
        purchase_exists = Purchase.objects.filter(user=author, work=work).exists()
        assert purchase_exists is False, "Автор не может купить свою работу"

    def test_cannot_purchase_already_purchased_work(self, client):
        """Нельзя купить уже купленную работу"""
        author = AuthorFactory()
        user = UserFactory()

        user.refresh_from_db()
        user.profile.balance = Decimal('200.00')
        user.profile.save()

        work = PaidWorkFactory(author=author)

        client.login(username=user.username, password='testpass123')

        # Первая покупка
        response1 = client.post(reverse('works:purchase_work', args=[work.id]))
        assert response1.status_code == 302, f"Первая покупка должна вернуть редирект 302, получен {response1.status_code}"

        # Вторая покупка
        response2 = client.post(reverse('works:purchase_work', args=[work.id]))
        assert response2.status_code == 302, f"Вторая попытка должна вернуть редирект 302, получен {response2.status_code}"

        # Должна быть только одна покупка
        purchase_count = Purchase.objects.filter(user=user, work=work).count()
        assert purchase_count == 1, "Нельзя купить работу дважды"