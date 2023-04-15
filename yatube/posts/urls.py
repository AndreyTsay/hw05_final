from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = 'posts'
urlpatterns = [path('', views.index, name='index'),
               path('group/<slug:slug>/',
                    views.group_list, name='group_list'),
               path('profile/<str:username>/', views.profile, name='profile'),
               path('posts/<int:post_id>/',
                    views.post_detail, name='post_detail'),
               path("create/", views.create_post, name="create_post"),
               path("posts/<int:post_id>/edit/",
                    views.post_edit, name="post_edit"),
               ]
handler404 = 'core.views.page_not_found'
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
