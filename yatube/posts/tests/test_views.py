import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
# from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse
from django import forms

from posts.models import Comment, Group, Follow, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    """Тестирование страниц во вью-функциях в приложении Posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='Something'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )
        cls.group_1 = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test_group'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_in_the_right_group(self):
        """ Проверяем что пост попал в нужную группу """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'Something'}))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_not_in_the_other_group(self):
        """ Проверяем что пост не попал в другую группу """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_group'}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:main'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': 'Something'}
            ),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': 'StasBasov'}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            ),
            'posts/post_create.html': reverse('posts:post_create'),

        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    """Тест паджинатора страниц"""
    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='Something'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        for i in range(13):
            Post.objects.create(
                author=self.user,
                text='(Тестовый текст)*i',
                group=self.group,
            )

    def test_first_page_contains_ten_records_index(self):
        """Тестируем первую страницу главной страницы"""
        response = self.client.get(reverse('posts:main'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_index(self):
        """Тестируем вторую страницу главной страницы"""
        response = self.client.get(reverse('posts:main') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_group_list(self):
        """Тестируем первую страницу group_ist"""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'Something'}
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_group_list(self):
        """Тестируем вторую страницу траницу group_ist"""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'Something'}
        ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_profile(self):
        """Тестируем первую страницу gprofile"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'StasBasov'}
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_profile(self):
        """Тестируем вторую страницу траницу profile"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'StasBasov'}
        ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)


class YatubePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='Something',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:main'))
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.author.username
        task_text_0 = first_object.text
        task_slug_0 = first_object.group.title
        task_description_0 = first_object.group.description
        self.assertEqual(task_title_0, 'SomeUser')
        self.assertEqual(task_text_0, 'Тестовый текст')
        self.assertEqual(task_slug_0, 'Тестовый заголовок группы')
        self.assertEqual(task_description_0, 'Тестовое описание')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'Something'}
        ))
        first_object = response.context['page_obj'][0]
        title_1 = first_object.author.username
        text_1 = first_object.text
        tslug_1 = first_object.group.title
        description_1 = first_object.group.description
        self.assertEqual(title_1, 'SomeUser')
        self.assertEqual(text_1, 'Тестовый текст')
        self.assertEqual(tslug_1, 'Тестовый заголовок группы')
        self.assertEqual(description_1, 'Тестовое описание')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'SomeUser'}
        ))
        first_object = response.context['page_obj'][0]
        title_2 = first_object.author.username
        text_2 = first_object.text
        tslug_2 = first_object.group.title
        description_2 = first_object.group.description
        self.assertEqual(title_2, 'SomeUser')
        self.assertEqual(text_2, 'Тестовый текст')
        self.assertEqual(tslug_2, 'Тестовый заголовок группы')
        self.assertEqual(description_2, 'Тестовое описание')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        self.assertEqual(response.context.get('post').text, self.post.text)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageExistTest(TestCase):
    """Проверка картинок в контексте шаблонов"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username='SomeUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='Something'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_has_image(self):
        response = self.authorized_client.get(
            reverse(
                'posts:main'
            )
        )
        test_object = response.context['page_obj'][0]
        post_image = test_object.image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_profile_has_image(self):
        response = self.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': 'SomeUser'}
            )
        )
        test_object = response.context['page_obj'][0]
        post_image = test_object.image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_group_list_has_image(self):
        response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': 'Something'}
            )
        )
        test_object = response.context['page_obj'][0]
        post_image = test_object.image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_post_detail_has_image(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            )
        )
        test_object = response.context['post']
        post_image = test_object.image
        self.assertEqual(post_image, 'posts/small.gif')


class CashingIndexTest(TestCase):
    """Проверка кеширования главной страницы"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeUser')
        cls.post_cache = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_cache(self):
        """Тестируем кэш главной страницы"""
        response = self.authorized_client.get(
            reverse('posts:main')
        ).content
        self.post_cache.delete()
        response_cache = self.authorized_client.get(
            reverse('posts:main')
        ).content
        self.assertEqual(response, response_cache)

        cache.clear()
        response_clear = self.authorized_client.get(
            reverse('posts:main')
        )
        self.assertNotEqual(response, response_clear)


class SubscribeTests(TestCase):
    """Проверка подписок и все, что с ними связано"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower)
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )

    def setUp(self):
        self.follow = Follow.objects.get_or_create(
            user=self.follower,
            author=self.author
        )

    def test_subscribe_ability(self):
        self.follower_client.get(reverse(
            'posts:profile_follow', kwargs={
                'username': self.author.username
            }
        ))
        count_after_subs = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.author.username
            }
        ))
        count_after_unsubs = Follow.objects.count()
        self.assertNotEqual(count_after_subs, count_after_unsubs)

    def test_unsubscribe_ability(self):
        self.follower_client.get(reverse(
            'posts:profile_follow', kwargs={
                'username': self.author.username
            }
        ))
        count_before_unsubs = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.author.username
            }
        ))
        count_after_unsubs = Follow.objects.count()
        self.assertNotEqual(count_before_unsubs, count_after_unsubs)

    def test_post_in_subscribes(self):
        response = self.follower_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author.username
        post_text = first_object.text
        self.assertEqual(post_author, 'author')
        self.assertEqual(post_text, 'Тестовый текст')


class CommentTest(TestCase):
    """Проверка комментариев"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.postmaker = User.objects.create_user(username='postmaker')
        cls.postmaker_client = Client()
        cls.postmaker_client.force_login(cls.postmaker)
        cls.commentator = User.objects.create_user(username='commentator')
        cls.commentator_client = Client()
        cls.commentator_client.force_login(cls.commentator)
        cls.post = Post.objects.create(
            author=cls.postmaker,
            text='Тестовый текст',
        )

    def setUp(self):
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.commentator,
            text='Тестовый комментарий'
        )

    def test_comment_appear(self):
        self.assertTrue(Comment.objects.filter(
            post=self.post,
            author=self.commentator,
            text='Тестовый комментарий'
        ).exists)
