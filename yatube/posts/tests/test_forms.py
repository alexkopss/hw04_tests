import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Авторизуем пользователя."""
        self.authorized_author = Client()
        self.authorized_author.force_login(PostCreateFormTests.user)

    def test_creating_new_post(self):
        """Проверяем создание нового поста"""
        posts_count = Post.objects.count() + 1
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст из формы',
            'image': uploaded,
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
        self.assertTrue(
            Post.objects.filter(
                text='Текст из формы',
                image='posts/small.gif'
            ).exists()
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
