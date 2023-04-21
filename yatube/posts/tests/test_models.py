from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, TEXT_LENGTH

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names_for_group(self):
        """Проверяем, что у моделей корректно работает __str__ у group."""
        test_group_tittle = PostModelTest.group
        expected_group_name = self.group.title
        self.assertEqual(expected_group_name, str(test_group_tittle))

    def test_models_have_correct_object_names_for_post(self):
        """Проверяем, что у моделей корректно работает __str__ у post."""
        test_post_tittle = PostModelTest.post
        expected_post_name = self.post.text[:TEXT_LENGTH]
        self.assertEqual(expected_post_name, str(test_post_tittle))
