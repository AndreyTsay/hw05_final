import shutil
import tempfile
import posts.tests.constants as ct
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post
from posts.views import NUMBER_OF_POSTS

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
        """"Тест пагинатора на странице index"""
        response = self.client.get(reverse(ct.INDEX_URL_NAME, kwargs={}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        page_obj = response.context.get('page_obj')
        self.assertIsNotNone(page_obj)
        self.assertIsInstance(page_obj, Page)
        self.assertQuerysetEqual(
            page_obj, Post.objects.all()[:NUMBER_OF_POSTS], lambda x: x)

    def test_paginator_group_list(self):
        """Тест пагинатора на странице group_list"""
        response = self.client.get(
            reverse(ct.GROUP_LIST_URL_NAME,
                    kwargs=({'slug': self.group.slug})))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        page_obj = response.context.get('page_obj')
        self.assertIsNotNone(page_obj)
        self.assertIsInstance(page_obj, Page)
        self.assertQuerysetEqual(
            page_obj, (self.group.posts.all()[:NUMBER_OF_POSTS]), lambda x: x)

    def test_paginator_profile(self):
        """Тест пагинатора на странице profile"""
        response = self.client.get(
            reverse(ct.PROFILE_URL_NAME,
                    kwargs=({'username': self.user.username})))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        page_obj = response.context.get('page_obj')
        self.assertIsNotNone(page_obj)
        self.assertIsInstance(page_obj, Page)
        self.assertQuerysetEqual(
            page_obj, self.user.posts.all()[:NUMBER_OF_POSTS], lambda x: x)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagesTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_templates(self):
        """Тест формирования правильных шаблонов страниц: index, group_list,
        profile, post_detail, post_edit, post_create"""
        data = {
            ct.INDEX_URL_NAME: (
                ct.INDEX_TEMPLATE, {}
            ),
            ct.GROUP_LIST_URL_NAME: (
                ct.GROUP_LIST_TEMPLATE, {'slug': self.group.slug}
            ),
            ct.PROFILE_URL_NAME: (
                ct.PROFILE_URL_TEMPLATE, {'username': self.user.username}
            ),
            ct.POST_DETAIL_URL_NAME: (
                ct.POST_DETAIL_URL_TEMPLATE, {'post_id': self.post.id}
            ),
            ct.POST_EDIT_URL_NAME: (
                ct.POST_EDIT_URL_NAME_TEMPLATE, {'post_id': self.post.id}
            ),
            ct.POST_CREATE_URL_NAME: (
                ct.POST_CREATE_URL_TEMPLATE, {}
            ),
        }
        for url_name, params in data.items():
            with self.subTest(url_name=url_name):
                template, kwargs = params
                response = self.authorized_client.get(
                    reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_posts_index_page_show_correct_context(self):
        """Шаблон posts/index сформирован с правильным контекстом."""
        response = self.client.get(reverse(ct.INDEX_URL_NAME))
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
            reverse(ct.GROUP_LIST_URL_NAME, kwargs={"slug": self.group.slug})
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
            reverse(ct.PROFILE_URL_NAME, args=(self.user.username,))
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
            reverse(ct.POST_DETAIL_URL_NAME, kwargs={'post_id': self.post.id}))
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
            reverse(ct.POST_CREATE_URL_NAME))
        self.assertIn('form', response.context)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        response = self.authorized_client.get(
            reverse(ct.GROUP_LIST_URL_NAME, kwargs={"slug": self.group.slug}))
        self.assertNotIn(
            Post.objects.exclude(group=self.post.group),
            response.context.get("page_obj"))

    def test_comment_correct_context(self):
        """Валидная форма Комментария создает запись в Post."""
        comments_count = Comment.objects.count()
        form_data = {"text": "Тестовый коммент"}
        response = self.authorized_client.post(
            reverse(ct.POST_ADD_COMMENT, kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(ct.POST_DETAIL_URL_NAME,
                              kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter
                        (text="Тестовый коммент").exists())

    def test_check_cache(self):
        """Проверка кеша."""
        response_to_page = self.client.get(reverse(ct.INDEX_URL_NAME))
        content_of_responsed_page = response_to_page.content
        Post.objects.get(id=1).delete()
        response_to_cache_page = self.client.get(reverse(ct.INDEX_URL_NAME))
        content_of_cached_page = response_to_cache_page.content
        self.assertEqual(content_of_responsed_page, content_of_cached_page)

    def test_count_profile_without_follows(self):
        response_to_folow_page = self.authorized_client.get(
            reverse(ct.FOLLOW_INDEX_URL_NAME))
        self.assertEqual(len(response_to_folow_page.context["page_obj"]), 0)

    def test_follow_page(self):
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response_to_check_follows = self.authorized_client.get(
            reverse(ct.FOLLOW_INDEX_URL_NAME))
        self.assertEqual(len(response_to_check_follows.context["page_obj"]), 1)
        self.assertIn(self.post, response_to_check_follows.context["page_obj"])

    def test_follow_page_another_author(self):
        outsider = User.objects.create(username="NoName")
        self.authorized_client.force_login(outsider)
        respose = self.authorized_client.get(
            reverse(ct.FOLLOW_INDEX_URL_NAME))
        self.assertNotIn(self.post, respose.context["page_obj"])

    def test_profile_follows_after_delete(self):
        respose = self.authorized_client.get(
            reverse(ct.FOLLOW_INDEX_URL_NAME))
        self.assertEqual(len(respose.context["page_obj"]), 0)

    def test_image_in_group_list_page(self):
        """Картинка передается на страницу group_list."""
        response = self.client.get(
            reverse(ct.GROUP_LIST_URL_NAME, kwargs={"slug": self.group.slug}),
        )
        self.assertEqual(
            response.context["page_obj"][0].image, self.post.image)

    def test_image_in_index_and_profile_page(self):
        """Картинка передается на страницу index"""
        response = self.client.get(reverse(ct.INDEX_URL_NAME))
        self.assertEqual(
            response.context["page_obj"][0].image, self.post.image)

    def test_image_in_profile_page(self):
        """Картинка передается на страницу profile."""
        response = self.client.get(reverse(ct.PROFILE_URL_NAME,
                                   kwargs={"username": self.post.author}),)
        response_to_context = response.context["page_obj"][0]
        self.assertEqual(response_to_context.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.client.get(
            reverse(ct.POST_DETAIL_URL_NAME, kwargs={"post_id": self.post.id})
        )
        response_to_post_detail = response.context["post"]
        self.assertEqual(response_to_post_detail.image, self.post.image)

    def test_image_in_page(self):
        """Проверяем что пост с картинкой создается в БД"""
        self.assertTrue(
            Post.objects.filter(text="Тестовая запись",
                                image="posts/small.gif").exists()
        )
