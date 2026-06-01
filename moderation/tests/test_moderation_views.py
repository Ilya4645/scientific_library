import pytest
from django.urls import reverse
from works.tests.factories import WorkFactory, ApprovedWorkFactory
from accounts.tests.factories import AuthorFactory


@pytest.mark.django_db
class TestModerationViews:
    """Тесты представлений модерации"""

    def test_moderation_queue_requires_moderator(self, client, test_user):
        """Тест: очередь модерации требует прав модератора"""
        client.login(username=test_user.username, password='testpass123')
        response = client.get(reverse('moderation:queue'))
        assert response.status_code == 403

    def test_moderation_queue_accessible_by_moderator(self, moderator_client):
        """Тест: очередь модерации доступна модератору"""
        response = moderator_client.get(reverse('moderation:queue'))
        assert response.status_code == 200
        assert 'moderation/queue.html' in [t.name for t in response.templates]

    def test_moderation_queue_shows_only_pending_works(self, moderator_client, test_author):
        """Тест: очередь показывает только работы на модерации"""
        pending_work = WorkFactory(author=test_author, title='Pending Work', moderation_status='pending')
        approved_work = ApprovedWorkFactory(author=test_author, title='Approved Work')

        response = moderator_client.get(reverse('moderation:queue'))
        content = response.content.decode()

        assert 'Pending Work' in content
        assert 'Approved Work' not in content

    def test_moderate_work_approve(self, moderator_client, test_author):
        """Тест: одобрение работы модератором"""
        work = WorkFactory(author=test_author, moderation_status='pending')

        response = moderator_client.post(
            reverse('moderation:moderate_work', args=[work.id]),
            {
                'moderation_status': 'approved',
                'moderation_comment': 'Работа одобрена'
            }
        )

        work.refresh_from_db()
        assert work.moderation_status == 'approved'
        assert work.moderation_comment == 'Работа одобрена'
        assert response.status_code == 302

    def test_moderate_work_reject(self, moderator_client, test_author):
        """Тест: отклонение работы модератором"""
        work = WorkFactory(author=test_author, moderation_status='pending')

        response = moderator_client.post(
            reverse('moderation:moderate_work', args=[work.id]),
            {
                'moderation_status': 'rejected',
                'moderation_comment': 'Работа не соответствует требованиям'
            }
        )

        work.refresh_from_db()
        assert work.moderation_status == 'rejected'
        assert work.moderation_comment == 'Работа не соответствует требованиям'
        assert response.status_code == 302

    def test_cannot_moderate_already_moderated_work(self, moderator_client, test_author):
        """Тест: нельзя модерировать уже обработанную работу"""
        work = ApprovedWorkFactory(author=test_author)

        response = moderator_client.post(
            reverse('moderation:moderate_work', args=[work.id]),
            {
                'moderation_status': 'rejected',
                'moderation_comment': 'Новое решение'
            }
        )

        work.refresh_from_db()
        # Статус должен остаться 'approved'
        assert work.moderation_status == 'approved'

    def test_moderation_queue_empty_message(self, moderator_client):
        """Тест: сообщение при пустой очереди модерации"""
        response = moderator_client.get(reverse('moderation:queue'))
        content = response.content.decode()

        assert 'Нет работ на модерации' in content or 'нет работ' in content.lower()