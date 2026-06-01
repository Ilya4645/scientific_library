from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
from .models import Work, Purchase, Category
from .forms import WorkCreateForm, WorkFilterForm
from accounts.decorators import role_required
from accounts.models import User
from decimal import Decimal
import os
import mimetypes
from django.http import StreamingHttpResponse, HttpResponse, Http404
from wsgiref.util import FileWrapper as FileWrapper2



def index(request):
    """Главная страница с топ-3 популярных работ и авторов"""

    # Топ-3 популярных работ (только одобренные)
    top_works = Work.objects.filter(
        moderation_status='approved'
    ).order_by('-downloads_count')[:3]

    # Топ-3 популярных авторов (только по одобренным работам)
    authors_data = []
    authors = User.objects.filter(
        role__in=['author', 'moderator', 'admin']
    )

    for author in authors:
        total_downloads = Work.objects.filter(
            author=author,
            moderation_status='approved'
        ).aggregate(total=Sum('downloads_count'))['total'] or 0

        if total_downloads > 0:
            authors_data.append({
                'author': author,
                'total_downloads': total_downloads
            })

    authors_data.sort(key=lambda x: x['total_downloads'], reverse=True)
    top_authors = [item['author'] for item in authors_data[:3]]

    if len(top_authors) < 3:
        existing_ids = [author.id for author in top_authors]
        other_authors = User.objects.filter(
            role__in=['author', 'moderator', 'admin'],
            works__moderation_status='approved'
        ).exclude(
            id__in=existing_ids
        ).distinct()[:3 - len(top_authors)]
        top_authors.extend(other_authors)

    # Последние добавленные работы
    recent_works = Work.objects.filter(
        moderation_status='approved'
    ).order_by('-published_at', '-created_at')[:6]

    # Статистика
    total_works = Work.objects.filter(moderation_status='approved').count()
    total_authors = User.objects.filter(
        role__in=['author', 'moderator', 'admin'],
        works__moderation_status='approved'
    ).distinct().count()
    total_downloads = Work.objects.filter(
        moderation_status='approved'
    ).aggregate(Sum('downloads_count'))['downloads_count__sum'] or 0
    free_works = Work.objects.filter(
        moderation_status='approved',
        price=0
    ).count()

    # Категории для фильтрации на главной
    categories = Category.objects.annotate(
        works_count=Count('works', filter=Q(works__moderation_status='approved'))
    ).filter(works_count__gt=0)[:6]

    context = {
        'top_works': top_works,
        'top_authors': top_authors,
        'recent_works': recent_works,
        'total_works': total_works,
        'total_authors': total_authors,
        'total_downloads': total_downloads,
        'free_works': free_works,
        'categories': categories,
    }
    return render(request, 'index.html', context)


def work_list(request):
    """Список всех одобренных работ с фильтрацией"""
    works = Work.objects.filter(moderation_status='approved')

    # Обработка формы фильтрации
    form = WorkFilterForm(request.GET)

    if form.is_valid():
        # Поиск
        search_query = form.cleaned_data.get('search')
        if search_query:
            works = works.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(author__username__icontains=search_query)
            )

        # Фильтр по цене
        price_filter = form.cleaned_data.get('price')
        if price_filter == 'free':
            works = works.filter(price=0)
        elif price_filter == 'paid':
            works = works.filter(price__gt=0)

        # Фильтр по категориям (теперь может быть несколько категорий)
        categories = form.cleaned_data.get('categories')
        if categories:
            works = works.filter(categories__in=categories).distinct()

    # Пагинация
    paginator = Paginator(works, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Категории для отображения в фильтре с количеством работ
    all_categories = Category.objects.annotate(
        works_count=Count('works', filter=Q(works__moderation_status='approved'))
    ).filter(works_count__gt=0)

    selected_categories = request.GET.getlist('categories')

    context = {
        'works': page_obj,
        'form': form,
        'categories': all_categories,
        'selected_categories': [int(c) for c in selected_categories if c.isdigit()],
        'search_query': form.cleaned_data.get('search', '') if form.is_valid() else '',
        'price_filter': form.cleaned_data.get('price', '') if form.is_valid() else '',
    }
    return render(request, 'works/work_list.html', context)


def work_detail(request, work_id):
    """Детальная страница работы - только для одобренных работ"""
    work = get_object_or_404(Work, id=work_id)

    # Если работа не одобрена, показываем 404 или специальную страницу
    if work.moderation_status != 'approved':
        # Для автора работы показываем специальное сообщение
        if request.user.is_authenticated and request.user == work.author:
            messages.warning(request,
                             f'Эта работа еще не опубликована. Текущий статус: {work.get_moderation_status_display()}')
            return redirect('works:my_works')
        else:
            raise Http404("Работа не найдена или еще не опубликована")

    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = Purchase.objects.filter(user=request.user, work=work).exists()

    # Похожие работы (по категориям)
    similar_works = Work.objects.filter(
        moderation_status='approved',
        categories__in=work.categories.all()
    ).exclude(id=work.id).distinct()[:3]

    context = {
        'work': work,
        'has_purchased': has_purchased,
        'similar_works': similar_works,
    }
    return render(request, 'works/work_detail.html', context)


@login_required
@role_required(['author', 'moderator', 'admin'])
def work_create(request):
    """Создание новой работы"""
    if request.method == 'POST':
        form = WorkCreateForm(request.POST, request.FILES)
        if form.is_valid():
            work = form.save(commit=False)
            work.author = request.user
            work.save()
            form.save_m2m()  # Сохраняем связи многие-ко-многим (категории)
            messages.success(request, 'Работа отправлена на модерацию!')
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
    """Скачивание работы - альтернативная версия"""
    work = get_object_or_404(Work, id=work_id, moderation_status='approved')

    # Проверяем статус работы
    if work.moderation_status != 'approved':
        messages.error(request, 'Эта работа еще не опубликована и недоступна для скачивания')
        return redirect('works:my_works')

    # Проверка прав на скачивание
    if not work.can_download(request.user):
        messages.error(request, 'У вас нет прав на скачивание этой работы')
        return redirect('works:work_detail', work_id=work_id)

    # Проверяем, существует ли файл
    if not work.file:
        messages.error(request, 'Файл работы не найден')
        return redirect('works:work_detail', work_id=work_id)

    # Получаем путь к файлу
    file_path = work.file.path

    # Проверяем, существует ли файл на диске
    if not os.path.exists(file_path):
        messages.error(request, 'Файл не найден на сервере')
        return redirect('works:work_detail', work_id=work_id)

    # Увеличиваем счетчик скачиваний
    work.downloads_count += 1
    work.save()

    # Получаем оригинальное имя файла
    original_filename = os.path.basename(work.file.name)

    # Определяем MIME-тип файла
    mime_type, encoding = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    # Открываем файл и возвращаем его
    wrapper = FileWrapper2(open(file_path, 'rb'))
    response = StreamingHttpResponse(wrapper, content_type=mime_type)
    response['Content-Disposition'] = f'attachment; filename="{original_filename}"'
    response['Content-Length'] = os.path.getsize(file_path)

    return response


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
            amount_decimal = Decimal(str(work.price))
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


@login_required
def work_edit(request, work_id):
    """Редактирование отклоненной работы для повторной отправки"""
    work = get_object_or_404(Work, id=work_id, author=request.user)

    # Только отклоненные работы можно редактировать
    if work.moderation_status != 'rejected':
        messages.error(request, 'Редактирование доступно только для отклоненных работ')
        return redirect('works:my_works')

    if request.method == 'POST':
        form = WorkCreateForm(request.POST, request.FILES, instance=work)
        if form.is_valid():
            edited_work = form.save(commit=False)
            edited_work.moderation_status = 'pending'  # Снова отправляем на модерацию
            edited_work.moderation_comment = ''  # Очищаем комментарий модератора
            edited_work.save()
            form.save_m2m()  # Сохраняем категории
            messages.success(request, 'Работа отправлена на повторную модерацию!')
            return redirect('works:my_works')
    else:
        form = WorkCreateForm(instance=work)

    context = {
        'form': form,
        'work': work,
        'is_editing': True
    }
    return render(request, 'works/work_edit.html', context)