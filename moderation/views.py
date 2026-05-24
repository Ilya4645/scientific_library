from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from works.models import Work
from accounts.decorators import moderator_required


@moderator_required
def moderation_queue(request):
    pending_works = Work.objects.filter(moderation_status='pending').order_by('-created_at')
    return render(request, 'moderation/queue.html', {'works': pending_works})


@moderator_required
def moderate_work(request, work_id):
    work = get_object_or_404(Work, id=work_id)

    if request.method == 'POST':
        status = request.POST.get('moderation_status')
        comment = request.POST.get('moderation_comment', '')

        work.moderation_status = status
        work.moderation_comment = comment

        if status == 'approved':
            work.published_at = timezone.now()

        work.save()

        status_text = 'одобрена' if status == 'approved' else 'отклонена'
        messages.success(request, f'Работа "{work.title}" {status_text}')
        return redirect('moderation:queue')

    return redirect('moderation:queue')