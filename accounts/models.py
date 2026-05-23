from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class User(AbstractUser):
    """
    Расширенная модель пользователя с ролями
    """
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('author', 'Автор'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def can_publish(self):
        """Может ли пользователь публиковать работы"""
        return self.role in ['author', 'moderator', 'admin']

    def is_moderator(self):
        return self.role in ['moderator', 'admin']

    def clean(self):
        if self.username and len(self.username) < 3:
            raise ValidationError({'username': 'Имя пользователя должно содержать минимум 3 символа'})


class UserProfile(models.Model):
    """
    Профиль пользователя (связь 1:1 с User)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    institution = models.CharField(max_length=200, blank=True, help_text="Научное учреждение")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Профиль {self.user.username}"

    def add_balance(self, amount):
        """Пополнение баланса"""
        if amount < 0:
            raise ValidationError("Сумма не может быть отрицательной")
        self.balance += amount
        self.save()

    def deduct_balance(self, amount):
        """Списание с баланса"""
        if amount < 0:
            raise ValidationError("Сумма не может быть отрицательной")
        if self.balance < amount:
            raise ValidationError("Недостаточно средств")
        self.balance -= amount
        self.save()

    def clean(self):
        if self.balance < 0:
            raise ValidationError({'balance': 'Баланс не может быть отрицательным'})
