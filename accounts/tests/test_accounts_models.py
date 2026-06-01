import pytest
from django.core.exceptions import ValidationError
from decimal import Decimal
from accounts.models import User, UserProfile
from accounts.tests.factories import UserFactory, AuthorFactory


@pytest.mark.django_db
class TestUserModel:
    """Тесты модели User"""

    def test_create_user(self):
        """Создание пользователя"""
        user = UserFactory()
        assert user.username is not None
        assert user.email is not None
        assert user.check_password('testpass123')
        assert user.role == 'user'

    def test_create_author(self):
        """Создание автора"""
        author = AuthorFactory()
        assert author.role == 'author'
        assert author.can_publish() is True

    def test_user_str_method(self):
        """Метод __str__"""
        user = UserFactory(username='testuser')
        expected = f"testuser (Пользователь)"
        assert str(user) == expected

    def test_get_total_downloads_method(self):
        """Метод get_total_downloads"""
        from works.tests.factories import ApprovedWorkFactory, WorkFactory

        author = AuthorFactory()

        # Создаем работы
        work1 = ApprovedWorkFactory(author=author, downloads_count=10)
        work2 = ApprovedWorkFactory(author=author, downloads_count=20)
        work3 = WorkFactory(author=author, downloads_count=30, moderation_status='rejected')

        total = author.get_total_downloads()
        assert total == 30  # 10 + 20

    def test_get_approved_works_count_method(self):
        """Метод get_approved_works_count"""
        from works.tests.factories import WorkFactory, ApprovedWorkFactory

        author = AuthorFactory()

        ApprovedWorkFactory(author=author)
        ApprovedWorkFactory(author=author)
        WorkFactory(author=author, moderation_status='pending')
        WorkFactory(author=author, moderation_status='rejected')

        count = author.get_approved_works_count()
        assert count == 2

    def test_user_validation_username_too_short(self):
        """Валидация: имя пользователя слишком короткое"""
        user = User(username='ab', email='test@example.com')
        with pytest.raises(ValidationError):
            user.full_clean()

    def test_unique_email_constraint(self):
        """Уникальность email"""
        UserFactory(email='unique@example.com')
        with pytest.raises(Exception):
            UserFactory(email='unique@example.com')


@pytest.mark.django_db
class TestUserProfileModel:
    """Тесты модели UserProfile"""

    def test_profile_created_automatically(self):
        """Профиль создается автоматически"""
        user = UserFactory()
        user.refresh_from_db()
        assert hasattr(user, 'profile'), "У пользователя должен быть профиль"
        assert user.profile.balance == 0

    def test_profile_str_method(self):
        """Метод __str__ профиля"""
        user = UserFactory()
        user.refresh_from_db()
        expected = f"Профиль {user.username}"
        assert str(user.profile) == expected

    def test_add_balance(self):
        """Пополнение баланса"""
        user = UserFactory()
        user.refresh_from_db()
        user.profile.add_balance(Decimal('100.50'))
        user.refresh_from_db()
        assert user.profile.balance == Decimal('100.50')

    def test_add_balance_negative_amount_raises_error(self):
        """Пополнение на отрицательную сумму - ошибка"""
        user = UserFactory()
        user.refresh_from_db()
        with pytest.raises(ValidationError, match="Сумма не может быть отрицательной"):
            user.profile.add_balance(Decimal('-50'))

    def test_deduct_balance(self):
        """Списание с баланса"""
        user = UserFactory()
        user.refresh_from_db()
        user.profile.add_balance(Decimal('100'))
        user.profile.deduct_balance(Decimal('30'))
        user.refresh_from_db()
        assert user.profile.balance == Decimal('70')

    def test_deduct_balance_insufficient_funds_raises_error(self):
        """Списание при недостатке средств - ошибка"""
        user = UserFactory()
        user.refresh_from_db()
        user.profile.add_balance(Decimal('50'))
        with pytest.raises(ValidationError, match="Недостаточно средств"):
            user.profile.deduct_balance(Decimal('100'))

    def test_deduct_balance_negative_amount_raises_error(self):
        """Списание отрицательной суммы - ошибка"""
        user = UserFactory()
        user.refresh_from_db()
        with pytest.raises(ValidationError, match="Сумма не может быть отрицательной"):
            user.profile.deduct_balance(Decimal('-10'))

    def test_profile_balance_negative_validation(self):
        """Валидация отрицательного баланса"""
        user = UserFactory()
        user.refresh_from_db()
        user.profile.balance = Decimal('-10')
        with pytest.raises(ValidationError):
            user.profile.clean()