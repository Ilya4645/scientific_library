from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse
from django.template.loader import render_to_string
from django.conf import settings

from django.core.exceptions import PermissionDenied
from .forms import RegistrationForm, UserProfileForm, BalanceTopUpForm,  PasswordResetRequestForm, PasswordResetConfirmForm
from .models import User
from .utils import generate_reset_token, verify_reset_token, delete_reset_token, cleanup_expired_tokens
from .email_backend import send_email

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        return '/'


def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('index')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)

    # Получаем покупки пользователя
    purchases = request.user.purchases.all().order_by('-purchase_date') if hasattr(request.user, 'purchases') else []

    context = {
        'form': form,
        'profile': profile,
        'purchases': purchases,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def top_up_balance(request):
    if request.method == 'POST':
        form = BalanceTopUpForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            request.user.profile.add_balance(amount)
            messages.success(request, f'Баланс пополнен на {amount} ₽')
            return redirect('accounts:profile')
    else:
        form = BalanceTopUpForm()

    return render(request, 'accounts/top_up_balance.html', {'form': form})


@login_required
def author_detail(request, user_id):
    author = get_object_or_404(User, id=user_id)

    if author.role not in ['author', 'moderator', 'admin']:
        raise PermissionDenied("Этот пользователь не является автором")

    works = author.works.filter(moderation_status='approved')

    context = {
        'author': author,
        'works': works,
    }
    return render(request, 'accounts/author_detail.html', context)


@login_required
def become_author(request):
    """Страница становления автором"""
    # Если пользователь уже автор
    if request.user.role in ['author', 'moderator', 'admin']:
        messages.info(request, 'Вы уже являетесь автором!')
        return redirect('accounts:profile')

    if request.method == 'POST':
        # Проверяем, что пользователь согласился с правилами
        request.user.role = 'author'
        request.user.save()
        messages.success(request, 'Поздравляем! Теперь вы можете публиковать свои научные работы!')
        return redirect('works:work_create')  # Перенаправляем на создание первой работы

    return render(request, 'accounts/become_author.html')


def password_reset_request(request):
    """Запрос на восстановление пароля"""
    cleanup_expired_tokens()

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Генерируем токен
            token = generate_reset_token(email)

            # Создаем ссылку для сброса
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'token': token})
            )

            # Создаем содержимое письма
            subject = "Восстановление пароля на Scientific Library"

            # Текстовая версия
            text_message = render_to_string('emails/password_reset_email.txt', {
                'reset_url': reset_url
            })

            # HTML версия
            html_message = render_to_string('emails/password_reset_email.html', {
                'reset_url': reset_url
            })
            send_email(
                subject=subject,
                message=text_message,
                recipient_list=[email],
                html_message=html_message
            )

            messages.success(
                request,
                f'Инструкция по восстановлению пароля отправлена на {email}'
            )

            # Выводим ссылку в консоль для удобства
            print(f"\n🔐 Ссылка для восстановления пароля: {reset_url}\n")

            return redirect('accounts:password_reset_done')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_done(request):
    """Страница после отправки ссылки для восстановления"""
    backend_type = getattr(settings, 'EMAIL_BACKEND_TYPE', 'console')
    email_dir = getattr(settings, 'EMAIL_FILE_PATH', None)

    context = {
        'backend_type': backend_type,
        'email_dir': email_dir,
    }
    return render(request, 'accounts/password_reset_done.html', context)


def password_reset_confirm(request, token):
    """Подтверждение сброса пароля"""
    email = verify_reset_token(token)

    if not email:
        messages.error(request, 'Ссылка для восстановления пароля недействительна или истекла')
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']

            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()

                update_session_auth_hash(request, user)
                delete_reset_token(email)

                messages.success(request, 'Пароль успешно изменен! Теперь вы можете войти с новым паролем.')
                return redirect('accounts:login')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь не найден')
                return redirect('accounts:password_reset')
    else:
        form = PasswordResetConfirmForm()

    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'email': email})