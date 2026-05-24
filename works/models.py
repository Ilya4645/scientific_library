from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal


class Category(models.Model):
    """
    Категория научных работ (связь многие-ко-многим с Work)
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL-метка")
    description = models.TextField(blank=True, verbose_name="Описание категории")
    icon = models.CharField(max_length=50, blank=True, help_text="Иконка из Bootstrap Icons", verbose_name="Иконка")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Кастомная валидация категории"""
        if len(self.name) < 2:
            raise ValidationError({'name': 'Название категории должно содержать минимум 2 символа'})
        if not self.slug.isalnum() and '-' not in self.slug:
            raise ValidationError({'slug': 'Slug может содержать только буквы, цифры и дефисы'})

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Work(models.Model):
    """
    Научная работа (связь 1:N с автором, N:N с категориями)
    """
    STATUS_CHOICES = [
        ('pending', 'На модерации'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='works',
        verbose_name="Автор"
    )
    categories = models.ManyToManyField(
        Category,
        related_name='works',
        blank=True,
        verbose_name="Категории"
    )
    file = models.FileField(upload_to='works/%Y/%m/%d/', verbose_name="Файл работы", null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена")
    moderation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderation_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    downloads_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Работа"
        verbose_name_plural = "Работы"

    def __str__(self):
        return f"{self.title} - {self.author.username}"

    def clean(self):
        if self.price < 0:
            raise ValidationError({'price': 'Цена не может быть отрицательной'})
        if self.price > 0 and not self.file:
            raise ValidationError({'file': 'Для платной работы необходимо загрузить файл'})
        if len(self.title) < 5:
            raise ValidationError({'title': 'Название должно содержать минимум 5 символов'})

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.moderation_status == 'approved' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def is_free(self):
        return self.price == 0

    def can_download(self, user):
        if not user.is_authenticated:
            return False
        if self.is_free():
            return True
        from .models import Purchase
        return Purchase.objects.filter(user=user, work=self).exists()

    def get_categories_list(self):
        """Возвращает список категорий для отображения"""
        return self.categories.all()


class Purchase(models.Model):
    """
    Покупка работы (связь N:N между User и Work)
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    author_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    purchase_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'work']
        verbose_name = "Покупка"
        verbose_name_plural = "Покупки"

    def __str__(self):
        return f"{self.user.username} купил {self.work.title}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма покупки должна быть положительной'})
        if self.user == self.work.author:
            raise ValidationError("Автор не может купить свою работу")
        if Purchase.objects.filter(user=self.user, work=self.work).exists():
            raise ValidationError("Вы уже приобрели эту работу")

    def save(self, *args, **kwargs):
        from decimal import Decimal
        if not self.pk:
            commission_rate = Decimal('0.10')
            self.commission = self.amount * commission_rate
            self.author_share = self.amount - self.commission
            self.user.profile.deduct_balance(self.amount)
            self.work.author.profile.add_balance(self.author_share)
        super().save(*args, **kwargs)