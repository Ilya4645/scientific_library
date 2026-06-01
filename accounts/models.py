from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


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

    def add_balance(self, amount):
        """Пополнение баланса"""
        amount_decimal = Decimal(str(amount))
        if amount_decimal < 0:
            raise ValidationError("Сумма не может быть отрицательной")
        self.balance += amount_decimal
        self.save()

    def deduct_balance(self, amount):
        """Списание с баланса"""
        amount_decimal = Decimal(str(amount))
        if amount_decimal < 0:
            raise ValidationError("Сумма не может быть отрицательной")
        if self.balance < amount_decimal:
            raise ValidationError("Недостаточно средств")
        self.balance -= amount_decimal
        self.save()

    def can_publish(self):
        """Может ли пользователь публиковать работы"""
        return self.role in ['author', 'moderator', 'admin']

    def is_moderator(self):
        return self.role in ['moderator', 'admin']

    def clean(self):
        if self.username and len(self.username) < 3:
            raise ValidationError({'username': 'Имя пользователя должно содержать минимум 3 символа'})

    def get_total_downloads(self):
        """Получить общее количество скачиваний всех одобренных работ автора"""
        from works.models import Work
        from django.db.models import Sum
        total = Work.objects.filter(
            author=self,
            moderation_status='approved'
        ).aggregate(total=Sum('downloads_count'))['total']
        return total or 0

    def get_approved_works_count(self):
        """Получить количество одобренных работ"""
        return self.works.filter(moderation_status='approved').count()


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
        # Конвертируем в Decimal
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        if amount < 0:
            raise ValidationError("Сумма не может быть отрицательной")

        # Обновляем баланс
        self.balance = Decimal(str(self.balance)) + amount
        self.save(update_fields=['balance'])

    def deduct_balance(self, amount):
        """Списание с баланса"""
        # Конвертируем в Decimal
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        if amount < 0:
            raise ValidationError("Сумма не может быть отрицательной")

        current_balance = Decimal(str(self.balance))
        if current_balance < amount:
            raise ValidationError("Недостаточно средств")

        self.balance = current_balance - amount
        self.save(update_fields=['balance'])

    def clean(self):
        if self.balance < 0:
            raise ValidationError({'balance': 'Баланс не может быть отрицательным'})

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создает профиль при создании нового пользователя"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

