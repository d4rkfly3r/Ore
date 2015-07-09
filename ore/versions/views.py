from ore.core.models import Namespace
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, CreateView, View, FormView, UpdateView, DeleteView, TemplateView, ListView
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.utils import lru_cache
from django.contrib import messages
from ore.projects.models import Project
from ore.projects.views import ProjectNavbarMixin
from ore.core.views import RequiresPermissionMixin, MultiFormMixin
from ore.versions.forms import NewVersionForm, VersionEditForm, VersionRenameForm, ChannelForm, NewFileForm
from ore.versions.models import Version, File, Channel

import os.path
import os
import uuid
import json


class ProjectsVersionsListView(ProjectNavbarMixin, ListView):

    model = Version

    template_name = 'repo/versions/list.html'
    context_object_name = 'versions'
    active_project_tab = 'versions'

    def get_project(self):
        return get_object_or_404(Project, name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])

    def get_queryset(self):
        project = self.get_project()
        qs = Version.objects.filter(project=project)
        channel = self.get_channel()
        if channel is not None:
            qs = qs.filter(channel=channel)
        return qs.as_user(self.request.user)

    def get_channel(self):
        channel_name = self.request.GET.get('channel', 'Release')
        if channel_name != 'all':
            return get_object_or_404(self.get_project().get_channels(), name=channel_name)
        return None

    def get_namespace(self):
        if not hasattr(self, "_namespace"):
            self._namespace = get_object_or_404(Namespace.objects.as_user(
                self.request.user).select_subclasses(), name=self.kwargs['namespace'])
            return self._namespace
        else:
            return self._namespace

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_channel'] = self.get_channel()
        context['namespace'] = self.get_namespace()
        context['proj'] = self.get_project()
        context['channels'] = self.get_project().get_channels()
        return context


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
        adding_files = File.objects.filter(
            project=project, status=File.STATUS.pending, version=None, id__in=self.request.POST.getlist('file')
        )
        adding_files.update(
            status=File.STATUS.active,
            version=self.object,
        )

        adding_files = File.objects.filter(
            project=project, version=self.object, id__in=self.request.POST.getlist('file')
        )
        for adding_file in adding_files:
            if adding_file.is_jar:
                adding_file.is_primary = True
                adding_file.save()
                break

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
        'edit': VersionEditForm,
        'rename': VersionRenameForm,
        'file_upload': NewFileForm,
    }

    def get_form_kwargs(self, form_name):
        kwargs = super().get_form_kwargs(form_name)
        if form_name == 'rename':
            kwargs['project'] = self.get_instance().project
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'namespace': self.kwargs['namespace'],
            'project': self.kwargs['project'],
            'proj': self.get_instance().project,
            'version': self.get_instance(),
        })
        return ctx

    def form_invalid(self, form_name, form):
        kwargs = self.get_context_data(**self.get_forms())
        kwargs['show_modal'] = form_name + '-modal'
        return self.render_to_response(kwargs)

    def form_valid(self, form_name, form):
        if form_name == 'file_upload':
            file = form.save(commit=False)
            file.version = self.get_instance()
            file.project = file.version.project
            file._update_attrs()
            if file.version.files.filter(file_name=file.file_name).count():
                # uh oh
                messages.error(
                    self.request, "Your file is named the same as a file already in this version. Try renaming it before uploading!")
            else:
                file.save()
                form.save_m2m()

                messages.success(
                    self.request, "Your file was uploaded successfully!")
            return self.get(self.request)
        else:
            form.save()
            messages.success(
                self.request, "Your changes were saved successfully!")
        return HttpResponseRedirect(self.get_form_instance(form_name).get_absolute_url())

    def get_form_instance(self, form_name):
        if form_name == 'file_upload':
            return None
        return self.get_instance()

    def get_instance(self):
        if '_instance' not in self.__dict__.keys():
            self._instance = self.get_queryset().get(
                **{self.slug_field: self.kwargs[self.slug_url_kwarg]})
        return self._instance

    def get_queryset(self):
        return Version.objects.as_user(self.request.user).filter(project__namespace__name=self.kwargs['namespace'], project__name=self.kwargs['project']).select_related('project')

    def post(self, request, *args, **kwargs):
        if self.request.POST.get('action') == 'delete_file':
            qs = self.get_instance().files.filter(
                id=self.request.POST.get('file_id'))
            if qs:
                qs.get().delete()
                messages.success(
                    self.request, "Your file was deleted successfully.")
        elif self.request.POST.get('action') == 'promote_file':
            qs = self.get_instance().files.filter(
                id=self.request.POST.get('file_id'))
            if qs:
                self.get_instance().files.update(is_primary=None)
                file = qs.get()
                file.is_primary = True
                file.save()
        return super().post(request, *args, **kwargs)


class ChannelsManageView(RequiresPermissionMixin, ProjectNavbarMixin, TemplateView):

    active_project_tab = 'manage'
    template_name = 'repo/versions/channels_manage.html'

    permissions = ['version.edit']

    def get_project(self):
        if getattr(self, '_project', None) is None:
            self._project = get_object_or_404(
                Project, name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])
        return self._project

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'namespace': self.kwargs['namespace'],
            'project': self.kwargs['project'],
            'proj': self.get_project(),
            'active_settings': 'channels',
            'channels': self.get_channels(),
            'create': self.get_create_form(),
        })
        return ctx

    def get_create_form(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'create' and not getattr(self, 'make_blank', False):
            data = self.request.POST
        else:
            data = None

        return ChannelForm(self.get_project(), data)

    def get_update_form(self, channel):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'update' and self.request.POST.get('old_id') == str(channel.id) and not getattr(self, 'make_blank', False):
            data = self.request.POST
        else:
            data = None

        return ChannelForm(self.get_project(), data, instance=channel)

    def get_channels(self):
        channels = self.get_project().get_channels()
        for channel in channels:
            if channel.project is not None:
                channel.update_form = self.get_update_form(channel)
        return channels

    def post(self, request, *args, **kwargs):
        self.make_blank = False
        if self.request.POST.get('action') == 'create':
            form = self.get_create_form()
            if form.is_valid():
                new_channel = form.save(commit=False)
                new_channel.project = self.get_project()
                new_channel.save()
                form.save_m2m()

                self.make_blank = True
                messages.success(
                    request, r"The channel was successfully created!")
        elif self.request.POST.get('action') == 'delete':
            channel = self.get_project().channels.get(
                id=self.request.POST.get('old_id'))
            message = ""
            if channel.versions.count():
                channel.versions.update(
                    channel=Channel.objects.get(name='Snapshot', project=None))
                message = " and the existing versions were reassigned into the 'Snapshot' channel"
            channel.delete()
            messages.success(
                request, r"The channel was successfully deleted{}!".format(message))
        elif self.request.POST.get('action') == 'update':
            channels = self.get_channels()
            for channel in channels:
                if str(channel.id) == self.request.POST.get('old_id'):
                    break
            else:
                return self.get(request, *args, **kwargs)

            channel.update_form.save()
            self.make_blank = True

            messages.success(
                request, r"The channel was successfully updated!")

        return self.get(request, *args, **kwargs)


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
