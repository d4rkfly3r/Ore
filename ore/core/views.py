from ore.accounts.models import OreUser
from ore.core import decorators
from ore.core.models import Namespace, Organization
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import FormView, DetailView, ListView, View
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from django.contrib.auth.decorators import login_required
from ore.projects.models import Project
from ore.teams.forms import TeamPermissionsForm
from django.contrib import messages

import crispy_forms.layout

class RequiresPermissionMixin(object):
    permissions = []

    def get_permissions(self):
        return self.permissions

    def dispatch(self, request, *args, **kwargs):
        return decorators.permission_required(
            self.get_permissions()
        )(
            super(RequiresPermissionMixin, self).dispatch
        )(request, *args, **kwargs)


class RequiresLoggedInMixin(object):

    def dispatch(self, request, *args, **kwargs):
        return login_required()(
            super(RequiresLoggedInMixin, self).dispatch
        )(request, *args, **kwargs)


class HomeView(View, TemplateResponseMixin, ContextMixin):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.is_authenticated():
            return self.render_to_response(template='home/user.html', context=context)
        else:
            return self.render_to_response(template='home/home.html', context=context)

    def render_to_response(self, context, template, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        return self.response_class(
            request=self.request,
            template=template,
            context=context,
            **response_kwargs
        )


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


class FormTestView(FormView):
    form_class = TeamPermissionsForm
    template_name = 'form_test.html'

    def form_valid(self, form):
        from pprint import pformat
        return HttpResponse(pformat(form.get_selected_permissions()), content_type='text/plain')


class MultiFormMixin(object):

    def get_forms(self):
        form_classes = self.form_classes
        out_forms = {}
        for form_name, form_class in self.form_classes.items():
            out_forms[form_name] = self.build_form(form_name, form_class)
        self.forms = out_forms
        return out_forms

    def build_form(self, form_name, form_class):
        form = form_class(**self.get_form_kwargs(form_name))
        if self.should_inject_hidden_element(form_name):
            form.helper.layout.append(crispy_forms.layout.Hidden(form_name, form_name))
        return form

    def get_form_kwargs(self, form_name):
        kwargs = {
            'initial': self.get_initial(form_name),
            'prefix': self.get_prefix(form_name),
        }

        instance = self.get_form_instance(form_name)
        if instance:
            kwargs['instance'] = instance

        if self.request.method in ('POST', 'PUT') and form_name in self.request.POST:
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_prefix(self, form_name):
        return form_name

    def get_initial(self, form_name):
        return {}

    def get_form_instance(self, form_name):
        return None

    def should_inject_hidden_element(self, form_name):
        return True

    def get(self, request, *args, **kwargs):
        forms = self.get_forms()
        return self.render_to_response(self.get_context_data(**forms))

    def form_valid(self, form_name, form):
        form.save()
        messages.success(self.request, "Your changes were saved successfully!")
        return HttpResponseRedirect(self.get_form_instance(form_name).get_absolute_url())

    def form_invalid(self, form_name, form):
        return self.render_to_response(self.get_context_data(self.forms))

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        for form_name, form in forms.items():
            if form_name in request.POST:
                if form.is_valid():
                    return self.form_valid(form_name, form)
                else:
                    return self.form_invalid(form_name, form)
        return self.get(request, *args, **kwargs)