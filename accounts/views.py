from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .forms import RegistrationForm, UserProfileForm, BalanceTopUpForm
from .models import User


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
    if request.method == 'POST':
        request.user.role = 'author'
        request.user.save()
        messages.success(request, 'Поздравляем! Теперь вы можете публиковать свои научные работы!')
        return redirect('accounts:profile')

    return render(request, 'accounts/become_author.html')