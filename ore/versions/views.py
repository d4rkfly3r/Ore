from ore.core.models import Namespace
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, CreateView, View, FormView, UpdateView, DeleteView, TemplateView
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from ore.projects.models import Project
from ore.projects.views import ProjectNavbarMixin
from ore.core.views import RequiresPermissionMixin, MultiFormMixin
from ore.versions.forms import NewVersionForm, VersionDescriptionForm, VersionRenameForm
from ore.versions.models import Version, File

import os.path
import os
import uuid
import json


class ProjectsVersionsListView(ProjectNavbarMixin, DetailView):

    model = Project
    slug_field = 'name'
    slug_url_kwarg = 'project'

    template_name = 'repo/versions/list.html'
    context_object_name = 'proj'
    active_project_tab = 'versions'

    def get_queryset(self):
        return Project.objects.filter(namespace__name=self.kwargs['namespace'])


class VersionsNewView(RequiresPermissionMixin, ProjectNavbarMixin, CreateView):

    model = Version
    template_name = 'repo/versions/new.html'

    form_class = NewVersionForm
    prefix = 'version'
    active_project_tab = 'versions'

    permissions = ['version.create', 'file.create']

    def get_project(self):
        return get_object_or_404(Project, name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])

    def get_context_data(self, **kwargs):
        data = super(VersionsNewView, self).get_context_data(**kwargs)
        data.update({
            'proj': self.get_project()
        })
        return data

    def form_valid(self, form):

        name = form.cleaned_data['name']
        project = self.get_project()

        if project.versions.filter(name=name).count():
            form.add_error(
                'name', 'That version name already exists in this project'
            )

        if not form.is_valid():
            return self.form_invalid(form)

        self.object = form.save()

        # now we handle the files themselves, if anywhere were uploaded
        File.objects.filter(
            project=project, status=File.STATUS.pending, version=None, id__in=self.request.POST.getlist('file')
        ).update(
            status=File.STATUS.active,
            version=self.object,
        )

        return super(VersionsNewView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(VersionsNewView, self).get_form_kwargs()
        if 'instance' not in kwargs or not kwargs['instance']:
            instance = self.model(project=self.get_project())
            kwargs.update({
                'instance': instance,
            })
        return kwargs


class VersionsDetailView(ProjectNavbarMixin, DetailView):

    model = Version
    slug_field = 'name'
    slug_url_kwarg = 'version'
    template_name = 'repo/versions/detail.html'
    active_project_tab = 'versions'

    def get_queryset(self):
        return Version.objects.as_user(self.request.user).filter(project__namespace__name=self.kwargs['namespace'], project__name=self.kwargs['project']).select_related('project')

    def get_namespace(self):
        if not hasattr(self, "_namespace"):
            self._namespace = get_object_or_404(Namespace.objects.as_user(
                self.request.user).select_subclasses(), name=self.kwargs['namespace'])
            return self._namespace
        else:
            return self._namespace

    def get_context_data(self, **kwargs):
        context = super(VersionsDetailView, self).get_context_data(**kwargs)
        context['namespace'] = self.get_namespace()
        context['proj'] = context['version'].project
        return context


# This view is only invoked internally by our Lua script running inside nginx
class VersionsCanCreateView(RequiresPermissionMixin, View):

    permissions = ['version.create', 'file.create']

    def get_project(self):
        return get_object_or_404(Project.objects.all().as_user(self.request.user), name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])

    def post(self, request, namespace, project):
        subdir_name = str(uuid.uuid4())
        subdir_name = os.path.join(
            subdir_name[0], subdir_name[0:2], subdir_name)

        composed = os.path.join(settings.MEDIA_ROOT, subdir_name)

        if not os.path.exists(composed):
            os.makedirs(composed)

        return JsonResponse({
            "upload_to": composed,
            "subdir_name": subdir_name,
        })


# This view is only invoked internally by our Lua script running inside nginx
class VersionsFileUploadedView(RequiresPermissionMixin, View):

    permissions = ['version.create', 'file.create']

    def get_project(self):
        return get_object_or_404(Project.objects.all().as_user(self.request.user), name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])

    def post(self, request, namespace, project):
        inp_data = json.loads(request.body.decode(request.encoding or 'utf-8'))
        f = File(
            project=self.get_project(),
            status=File.STATUS.pending,
            file=inp_data.get('file_path'),
            file_name=inp_data.get('file_name'),
            file_extension=inp_data.get('file_extension'),
            file_size=int(inp_data.get('file_size')),
            file_sha1=inp_data.get('file_sha1'),
        )
        f.save(update_file_attrs=False)
        return JsonResponse({
            'file_id': f.id,
            'file_name': inp_data.get('file_name'),
        })

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)



def forbidden(request):
    return HttpResponseForbidden("no")


class VersionsManageView(RequiresPermissionMixin, MultiFormMixin, ProjectNavbarMixin, TemplateView):

    model = Version
    slug_field = 'name'
    slug_url_kwarg = 'version'

    template_name = 'repo/versions/manage.html'
    context_object_name = 'proj'
    active_project_tab = 'manage'

    permissions = ['version.edit']

    form_classes = {
        'describe': VersionDescriptionForm,
        'rename': VersionRenameForm,
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'namespace': self.kwargs['namespace'],
            'project': self.kwargs['project'],
            'proj': self.get_instance().project,
            'version': self.get_instance(),
        })
        return ctx

    def get_form_instance(self, form_name):
        return self.get_instance()

    def get_instance(self):
        if not '_instance' in self.__dict__.keys():
            self._instance = self.get_queryset().get(**{self.slug_field: self.kwargs[self.slug_url_kwarg]})
        return self._instance

    def get_queryset(self):
        return Version.objects.as_user(self.request.user).filter(project__namespace__name=self.kwargs['namespace'], project__name=self.kwargs['project']).select_related('project')


class VersionsDeleteView(RequiresPermissionMixin, ProjectNavbarMixin, DeleteView):

    model = Version
    slug_field = 'name'
    slug_url_kwarg = 'version'

    template_name = 'repo/versions/manage.html'
    context_object_name = 'version'
    active_project_tab = 'manage'

    permissions = ['version.delete']

    def get_queryset(self):
        return Version.objects.filter(project__namespace__name=self.kwargs['namespace'], project__name=self.kwargs['project'])

    def get_success_url(self):
        return reverse('repo-versions-list', kwargs=dict(namespace=self.kwargs['namespace'], project=self.kwargs['project']))

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() == 'post':
            return super().dispatch(request, *args, **kwargs)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)