from http import HTTPStatus
import shutil
import tempfile


from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment, Follow
from posts.views import NUMBER_OF_POSTS
from posts.tests.constants import (

    GROUP_LIST_TEMPLATE,
    GROUP_LIST_URL_NAME,
    INDEX_TEMPLATE,
    INDEX_URL_NAME,
    PROFILE_URL_NAME,
    FOLLOW_INDEX_URL_NAME,
    PROFILE_URL_TEMPLATE,
    POST_DETAIL_URL_NAME,
    POST_DETAIL_URL_TEMPLATE,
    POST_EDIT_URL_NAME,
    POST_EDIT_URL_NAME_TEMPLATE,
    POST_CREATE_URL_NAME,
    POST_CREATE_URL_TEMPLATE,
    POST_ADD_COMMENT,
)

User = get_user_model()


class PaginatorViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='NAY')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug21',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Hoho',
            group=self.group,
        )

    def test_paginator_index(self):
        url_expected_post_number = {
            INDEX_URL_NAME: (
                {},
                Post.objects.all()[:NUMBER_OF_POSTS]
            ),
        }
        for url_name, params in url_expected_post_number.items():
            kwargs, queryset = params
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj, queryset, lambda x: x
                )

    def test_paginator_group_list(self):
        url_expected_post_number = {
            GROUP_LIST_URL_NAME: (
                {'slug': self.group.slug},
                self.group.posts.all()[:NUMBER_OF_POSTS]
            ),
        }
        for url_name, params in url_expected_post_number.items():
            kwargs, queryset = params
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj, queryset, lambda x: x
                )

    def test_paginator_profile(self):
        url_expected_post_number = {
            PROFILE_URL_NAME: (
                {'username': self.user.username},
                self.user.posts.all()[:NUMBER_OF_POSTS]
            ),
        }
        for url_name, params in url_expected_post_number.items():
            kwargs, queryset = params
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj, queryset, lambda x: x
                )

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile сформированы
        с правильным контекстом.
        """
        data = {
            INDEX_URL_NAME: (
                INDEX_TEMPLATE, {}
            ),
            GROUP_LIST_URL_NAME: (
                GROUP_LIST_TEMPLATE, {'slug': self.group.slug}
            ),
            PROFILE_URL_NAME: (
                PROFILE_URL_TEMPLATE, {'username': self.user.username}
            )}

        for url_name, params in data.items():
            with self.subTest(url_name=url_name):
                template, kwargs = params
                response = self.authorized_client.get(
                    reverse(url_name, kwargs=kwargs))
                page_obj = response.context.get('page_obj')
                text = self.post
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
                self.assertIn(text, page_obj)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NAY')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug21',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая запись",
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_templates(self):
        data = {
            INDEX_URL_NAME: (
                INDEX_TEMPLATE, {}
            ),
            GROUP_LIST_URL_NAME: (
                GROUP_LIST_TEMPLATE, {'slug': self.group.slug}
            ),
            PROFILE_URL_NAME: (
                PROFILE_URL_TEMPLATE, {'username': self.user.username}
            ),
            POST_DETAIL_URL_NAME: (
                POST_DETAIL_URL_TEMPLATE, {'post_id': self.post.id}
            ),
            POST_EDIT_URL_NAME: (
                POST_EDIT_URL_NAME_TEMPLATE, {'post_id': self.post.id}
            ),
            POST_CREATE_URL_NAME: (
                POST_CREATE_URL_TEMPLATE, {}
            ),
        }
        for url_name, params in data.items():
            with self.subTest(url_name=url_name):
                template, kwargs = params
                response = self.authorized_client.get(
                    reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_paginator_profile(self):
        url_expected_post_number = {
            PROFILE_URL_NAME: (
                {'username': self.user.username},
                self.user.posts.all()[:NUMBER_OF_POSTS]
            ),
        }
        for url_name, params in url_expected_post_number.items():
            kwargs, queryset = params
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj, queryset, lambda x: x
                )

    def test_posts_index_page_show_correct_context(self):
        """Шаблон posts/index сформирован с правильным контекстом."""
        response = self.client.get(reverse(INDEX_URL_NAME))
        page_context = (
            'title',
            'page_obj',
        )
        for value in page_context:
            self.assertIn(value, response.context)
        expected = list(Post.objects.all()[:NUMBER_OF_POSTS])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту."""
        response = self.client.get(
            reverse(GROUP_LIST_URL_NAME, kwargs={"slug": self.group.slug})
        )
        page_context = (
            'page_obj',
            'group',
        )
        for value in page_context:
            self.assertIn(value, response.context)
        expected = list(
            Post.objects.filter(group_id=self.group.id)[:NUMBER_OF_POSTS])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.client.get(
            reverse(PROFILE_URL_NAME, args=(self.user.username,))
        )
        page_context = (
            'page_obj',
            'author',
        )
        for value in page_context:
            self.assertIn(value, response.context)
        expected = list(
            Post.objects.filter(author_id=self.user.id)[:NUMBER_OF_POSTS])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(POST_DETAIL_URL_NAME, kwargs={'post_id': self.post.id}))
        page_context = (
            'post',
            'post_count',
        )
        for value in page_context:
            self.assertIn(value, response.context)
        response_to_post = response.context['post']
        post_text = {response_to_post.text: 'Тестовая запись',
                     response_to_post.group: self.group,
                     response_to_post.author: self.user.username}
        for value, expected in post_text.items():
            self.assertEqual(post_text[value], expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(POST_CREATE_URL_NAME))
        page_context = (
            'form',
        )
        for value in page_context:
            self.assertIn(value, response.context)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        form_fields = {
            reverse(
                GROUP_LIST_URL_NAME, kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context.get("page_obj")
                self.assertNotIn(expected, form_field)

    def test_comment_correct_context(self):
        """Валидная форма Комментария создает запись в Post."""
        comments_count = Comment.objects.count()
        form_data = {"text": "Тестовый коммент"}
        response = self.authorized_client.post(
            reverse(POST_ADD_COMMENT, kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(POST_DETAIL_URL_NAME,
                              kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter
                        (text="Тестовый коммент").exists())

    def test_check_cache(self):
        """Проверка кеша."""
        first_response_to_page = self.client.get(reverse(INDEX_URL_NAME))
        first_response_content = first_response_to_page.content
        Post.objects.get(id=1).delete()
        second_response_to_page = self.client.get(reverse(INDEX_URL_NAME))
        second_response_content = second_response_to_page.content
        self.assertEqual(first_response_content, second_response_content)

    def test_follow_page(self):
        response = self.authorized_client.get(reverse(FOLLOW_INDEX_URL_NAME))
        self.assertEqual(len(response.context["page_obj"]), 0)
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        r_2 = self.authorized_client.get(reverse(FOLLOW_INDEX_URL_NAME))
        self.assertEqual(len(r_2.context["page_obj"]), 1)
        self.assertIn(self.post, r_2.context["page_obj"])

        outsider = User.objects.create(username="NoName")
        self.authorized_client.force_login(outsider)
        r_2 = self.authorized_client.get(reverse(FOLLOW_INDEX_URL_NAME))
        self.assertNotIn(self.post, r_2.context["page_obj"])

        Follow.objects.all().delete()
        r_3 = self.authorized_client.get(reverse(FOLLOW_INDEX_URL_NAME))
        self.assertEqual(len(r_3.context["page_obj"]), 0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_image_in_group_list_page(self):
        """Картинка передается на страницу group_list."""
        response = self.client.get(
            reverse(GROUP_LIST_URL_NAME, kwargs={"slug": self.group.slug}),
        )
        obj = response.context["page_obj"][0]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_index_and_profile_page(self):
        """Картинка передается на страницу index_and_profile."""
        templates = (
            reverse(INDEX_URL_NAME),
            reverse(PROFILE_URL_NAME, kwargs={"username": self.post.author}),
        )
        for url in templates:
            with self.subTest(url):
                response = self.client.get(url)
                obj = response.context["page_obj"][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.client.get(
            reverse(POST_DETAIL_URL_NAME, kwargs={"post_id": self.post.id})
        )
        obj = response.context["post"]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        """Проверяем что пост с картинкой создается в БД"""
        self.assertTrue(
            Post.objects.filter(text="Тестовая запись",
                                image="posts/small.gif").exists()
        )
