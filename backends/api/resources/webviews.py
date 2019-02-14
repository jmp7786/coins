import requests
from django.shortcuts import redirect, render
from rest_framework.status import HTTP_200_OK

from models.admin_webviews import AdminWebview


def webview(request):
    name = request.GET.get('name')
    try:
        webview = AdminWebview.objects.get(webview_name=name)
    except AdminWebview.DoesNotExist:
        return render(request, 'templates/404.html')

    try:
        response = requests.get(webview.url)
        if response.status_code != HTTP_200_OK:
            return render(request, 'templates/500.html')
    except:
        return render(request, 'templates/500.html')

    return redirect(webview.url)
