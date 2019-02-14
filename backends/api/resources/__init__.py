from django.conf.urls import url

from .messages import MessageView
from .webviews import webview
from .notices import NoticeView, NoticeDetailView, ProfileAddtionalView

urls = [
    url(r'^notice/$', NoticeView.as_view()),
    url(r'^notice-detail/$', NoticeDetailView.as_view()),
    url(r'^profile-additional/$', ProfileAddtionalView.as_view()),
    url(r'^$', webview),
    url(r'^messages', MessageView.as_view()),

]
