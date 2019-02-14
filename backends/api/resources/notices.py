import re

from django.http import Http404
from django.shortcuts import render_to_response
from django.views.generic import TemplateView


class NoticeView(TemplateView):
    template_name = 'notice.html'


class NoticeDetailView(TemplateView):
    template_name = 'noticeDetail.html'


class ProfileAddtionalView(TemplateView):
    template_name = 'profileAdditional.html'

    def get(self, request, *args, **kwargs):

        gd = self.request.META.get('HTTP_GD')
        if gd:
            pattern = '(^([0-9]{3})([a-z]{2})@glowpick$)'
            matches = re.match(pattern, gd)
            if matches:
                context = self.get_context_data()
                return super(ProfileAddtionalView, self).render_to_response(context)
            else:
                raise Http404
        else:
            raise Http404


def page_not_found(request):
    response = render_to_response('error.html', {})
    response.status_code = 404
    return response


def server_error(request):
    response = render_to_response('error.html', {})
    response.status_code = 500
    return response
