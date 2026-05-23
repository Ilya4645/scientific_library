from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from .models import Work, Purchase
from .forms import WorkCreateForm
from accounts.decorators import role_required
from accounts.models import User


def index(request):
    # Топ-3 популярных работ
    top_works = Work.objects.filter(moderation_status='approved').order_by('-downloads_count')[:3]

    # Топ-3 популярных авторов
    top_authors = User.objects.filter(
        role__in=['author', 'moderator', 'admin'],
        works__moderation_status='approved'
    ).annotate(
        total_downloads=Sum('works__downloads_count')
    ).order_by('-total_downloads')[:3]

    # Последние работы
    recent_works = Work.objects.filter(moderation_status='approved').order_by('-published_at', '-created_at')[:6]

    # Статистика для главной страницы
    total_works = Work.objects.filter(moderation_status='approved').count()
    total_authors = User.objects.filter(role__in=['author', 'moderator', 'admin']).count()
    total_downloads = Work.objects.filter(moderation_status='approved').aggregate(Sum('downloads_count'))[
                          'downloads_count__sum'] or 0
    free_works = Work.objects.filter(moderation_status='approved', price=0).count()

    context = {
        'top_works': top_works,
        'top_authors': top_authors,
        'recent_works': recent_works,
        'total_works': total_works,
        'total_authors': total_authors,
        'total_downloads': total_downloads,
        'free_works': free_works,
    }
    return render(request, 'index.html', context)


def work_list(request):
    works = Work.objects.filter(moderation_status='approved')

    # Фильтрация
    price_filter = request.GET.get('price')
    if price_filter == 'free':
        works = works.filter(price=0)
    elif price_filter == 'paid':
        works = works.filter(price__gt=0)

    # Поиск
    search_query = request.GET.get('q')
    if search_query:
        works = works.filter(title__icontains=search_query)

    # Пагинация
    paginator = Paginator(works, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'works': page_obj,
        'search_query': search_query,
        'price_filter': price_filter,
    }
    return render(request, 'works/work_list.html', context)


def work_detail(request, work_id):
    work = get_object_or_404(Work, id=work_id, moderation_status='approved')

    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = Purchase.objects.filter(user=request.user, work=work).exists()

    similar_works = Work.objects.filter(
        author=work.author,
        moderation_status='approved'
    ).exclude(id=work.id)[:3]

    context = {
        'work': work,
        'has_purchased': has_purchased,
        'similar_works': similar_works,
    }
    return render(request, 'works/work_detail.html', context)


@login_required
@role_required(['author', 'moderator', 'admin'])
def work_create(request):
    if request.method == 'POST':
        form = WorkCreateForm(request.POST, request.FILES)
        if form.is_valid():
            work = form.save(commit=False)
            work.author = request.user
            work.save()
            messages.success(request, 'Работа отправлена на модерацию! После проверки она появится на сайте.')
            return redirect('works:my_works')
    else:
        form = WorkCreateForm()

    return render(request, 'works/work_create.html', {'form': form})


@login_required
def my_works(request):
    works = request.user.works.all().order_by('-created_at')
    return render(request, 'works/my_works.html', {'works': works})


@login_required
def download_work(request, work_id):
    work = get_object_or_404(Work, id=work_id, moderation_status='approved')

    if not work.can_download(request.user):
        messages.error(request, 'У вас нет прав на скачивание этой работы')
        return redirect('works:work_detail', work_id=work_id)

    work.downloads_count += 1
    work.save()

    if work.file:
        response = HttpResponse(work.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{work.file.name.split("/")[-1]}"'
        return response

    messages.error(request, 'Файл не найден')
    return redirect('works:work_detail', work_id=work_id)


@login_required
def purchase_work(request, work_id):
    work = get_object_or_404(Work, id=work_id, moderation_status='approved')

    if work.is_free():
        messages.error(request, 'Эта работа бесплатна, просто скачайте её')
        return redirect('works:work_detail', work_id=work_id)

    if request.user == work.author:
        messages.error(request, 'Вы не можете купить свою собственную работу')
        return redirect('works:work_detail', work_id=work_id)

    if Purchase.objects.filter(user=request.user, work=work).exists():
        messages.error(request, 'Вы уже приобрели эту работу')
        return redirect('works:work_detail', work_id=work_id)

    if request.user.profile.balance < work.price:
        messages.error(request, f'Недостаточно средств. Не хватает {work.price - request.user.profile.balance} ₽')
        return redirect('accounts:top_up_balance')

    if request.method == 'POST':
        try:
            Purchase.objects.create(
                user=request.user,
                work=work,
                amount=work.price
            )
            messages.success(request, f'Работа "{work.title}" успешно приобретена!')
            return redirect('works:work_detail', work_id=work_id)
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'works/purchase_confirm.html', {'work': work})