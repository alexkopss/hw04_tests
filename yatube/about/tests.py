from django.test import TestCase, Client
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()

    def test_static_page_accessability(self):
        """Проверка доступности статичных страниц"""
        rev_urls = {
            'about:author': 200,
            'about:tech': 200,
        }
        for rev, code in rev_urls.items():
            with self.subTest(rev=rev):
                response = self.guest_client.get(reverse(rev))
                self.assertEqual(response.status_code, code)

    def test_static_page_and_template(self):
        """Проверка статичных страниц"""
        templates_urls = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
