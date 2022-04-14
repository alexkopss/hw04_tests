from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    """Класс для провеки форм приложения 'posts'"""

    @classmethod
    def setUpClass(cls):
        """Добавляем во временную базу данных пользователя."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        """Авторизуем пользователя."""
        self.authorized_author = Client()
        self.authorized_author.force_login(PostCreateFormTests.user)

    def test_creating_new_post(self):
        """Проверяем создание нового поста"""
        posts_count = Post.objects.count() + 1
        form_data = {
            'text': 'Текст из формы',
        }
        self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            'Не удалось создать новый пост'
        )

    def test_editing_post(self):
        """Проверяем редактирование поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
        }
        self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertEqual(
            Post.objects.count(),
            posts_count,
            'Не удалось отредактироват пост'
        )
        self.assertEqual(
            self.post.text,
            form_data['text'],
            'Не удалось отредактироват пост'
        )
