from django.http import Http404
from django.shortcuts import render


def not_found(request):
    raise Http404()
