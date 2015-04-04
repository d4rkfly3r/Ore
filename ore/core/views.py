from ore.accounts.models import OreUser
from ore.core import decorators
from ore.core.models import Namespace, Organization
from django.http import HttpResponse

# Create your views here.
from django.views.generic import FormView, DetailView, ListView, View
from django.views.generic.base import TemplateResponseMixin, ContextMixin, TemplateView
from ore.projects.models import Project
from ore.teams.forms import TeamPermissionsForm


class RequiresPermissionMixin(object):
    permissions = []

    def get_permissions(self):
        return self.permissions

    def dispatch(self, request, *args, **kwargs):
        return decorators.permission_required(self.get_permissions())(super(RequiresPermissionMixin, self).dispatch)(request, *args, **kwargs)

class HomeView(View, TemplateResponseMixin, ContextMixin):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.is_authenticated():
            return self.render_to_response(template='home/user.html', context=context)
        else:
            return self.render_to_response(template='home/index.html', context=context)

    def render_to_response(self, context, template, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        return self.response_class(
            request=self.request,
            template=template,
            context=context,
            **response_kwargs
        )


class AppView(TemplateView):

    template_name = 'app.html'


class FormTestView(FormView):
    form_class = TeamPermissionsForm
    template_name = 'form_test.html'

    def form_valid(self, form):
        from pprint import pformat
        return HttpResponse(pformat(form.get_selected_permissions()), content_type='text/plain')


class NamespaceDetailView(DetailView):

    model = Namespace
    slug_field = 'name'
    slug_url_kwarg = 'namespace'

    def get_queryset(self, *args, **kwargs):
        qs = super(NamespaceDetailView, self).get_queryset(*args, **kwargs)
        qs = qs.select_subclasses()
        qs = qs.prefetch_related('projects')
        return qs

    def get_template_names(self):
        obj = self.object
        if isinstance(obj, OreUser):
            return ['repo/users/detail.html']
        elif isinstance(obj, Organization):
            return ['repo/orgs/detail.html']

        return super(NamespaceDetailView, self).get_template_names()


class ExploreView(ListView):

    def get_queryset(self):
        return Project.objects.as_user(self.request.user).select_related('namespace')

    template_name = 'repo/projects/index.html'
    context_object_name = 'projects'
