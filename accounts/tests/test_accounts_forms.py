import pytest
from accounts.forms import RegistrationForm, UserProfileForm, BalanceTopUpForm
from accounts.tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.form
class TestRegistrationForm:
    """Тесты формы регистрации"""

    def test_valid_registration_form(self):
        """Тест валидной формы регистрации"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }
        form = RegistrationForm(data=form_data)
        assert form.is_valid()

    @pytest.mark.parametrize('password,expected_valid', [
        ('123', False),  # слишком короткий
        ('weak', False),  # слишком короткий
        ('strongpassword123', True),  # хороший пароль
    ])
    def test_password_validation(self, password, expected_valid):
        """Тест валидации пароля"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': password,
            'password2': password
        }
        form = RegistrationForm(data=form_data)
        assert form.is_valid() == expected_valid

    def test_password_mismatch(self):
        """Тест несовпадения паролей"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'strongpass123',
            'password2': 'differentpass'
        }
        form = RegistrationForm(data=form_data)
        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_duplicate_email_validation(self):
        """Тест валидации уникальности email"""
        UserFactory(email='existing@example.com')

        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }
        form = RegistrationForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_invalid_email_format(self):
        """Тест невалидного формата email"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'strongpass123',
            'password2': 'strongpass123'
        }
        form = RegistrationForm(data=form_data)
        assert not form.is_valid()


@pytest.mark.django_db
@pytest.mark.form
class TestUserProfileForm:
    """Тесты формы профиля"""

    def test_valid_profile_form(self):
        """Тест валидной формы профиля"""
        form_data = {
            'bio': 'Это моя биография',
            'institution': 'МГУ'
        }
        form = UserProfileForm(data=form_data)
        assert form.is_valid()

    def test_profile_form_bio_too_long(self):
        """Тест биографии превышающей лимит"""
        form_data = {
            'bio': 'A' * 600,  # 600 символов, максимум 500
            'institution': 'МГУ'
        }
        form = UserProfileForm(data=form_data)
        assert not form.is_valid()
        assert 'bio' in form.errors

    def test_empty_bio_is_valid(self):
        """Тест пустой биографии"""
        form_data = {
            'bio': '',
            'institution': 'МГУ'
        }
        form = UserProfileForm(data=form_data)
        assert form.is_valid()

    def test_empty_institution_is_valid(self):
        """Тест пустого учреждения"""
        form_data = {
            'bio': 'Моя биография',
            'institution': ''
        }
        form = UserProfileForm(data=form_data)
        assert form.is_valid()


@pytest.mark.django_db
@pytest.mark.form
class TestBalanceTopUpForm:
    """Тесты формы пополнения баланса"""

    @pytest.mark.parametrize('amount', [
        '10.00', '100.50', '1', '9999.99'
    ])
    def test_valid_amounts(self, amount):
        """Тест валидных сумм пополнения"""
        form_data = {'amount': amount}
        form = BalanceTopUpForm(data=form_data)
        assert form.is_valid()

    @pytest.mark.parametrize('amount', [
        '-50', '0', '-0.01', 'abc', '100000'
    ])
    def test_invalid_amounts(self, amount):
        """Тест невалидных сумм пополнения"""
        form_data = {'amount': amount}
        form = BalanceTopUpForm(data=form_data)
        assert not form.is_valid()