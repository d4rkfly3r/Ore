from ore.core.models import Namespace
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import DetailView, CreateView, FormView, TemplateView
from ore.projects.models import Project, Channel
from ore.projects.views import ProjectNavbarMixin
from ore.core.views import RequiresPermissionMixin
from ore.versions.forms import NewVersionForm, NewVersionInnerFileFormset, NewChannelForm, ChannelDeleteForm
from ore.versions.models import Version, File


class ProjectsVersionsListView(ProjectNavbarMixin, DetailView):

    model = Project
    slug_field = 'name'
    slug_url_kwarg = 'project'

    template_name = 'versions/list.html'
    context_object_name = 'proj'
    active_project_tab = 'versions'

    def get_queryset(self):
        return Project.objects.filter(namespace__name=self.kwargs['namespace'])


class MultiFormMixin(object):
    multi_form_class = None
    multi_prefix = 'file'
    multi_initial = {}

    def get_multi_form_class(self):
        if self.multi_form_class is None:
            raise ValueError(
                "You must define multi_form_class or override get_multi_form_class!")
        return self.multi_form_class

    def get_multi_form_kwargs(self):
        kwargs = {
            'initial': self.get_multi_initial(),
            'prefix': self.get_multi_prefix(),
            'queryset': File.objects.none(),
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_multi_initial(self):
        return self.multi_initial.copy()

    def get_multi_prefix(self):
        return self.multi_prefix

    def get_multi_form(self, form_class):
        return form_class(**self.get_multi_form_kwargs())

    def get(self, request, *args, **kwargs):
        self.object = None

        multi_form_class = self.get_multi_form_class()
        multi_form = self.get_multi_form(multi_form_class)

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        return self.render_to_response(self.get_context_data(form=form, multi_form=multi_form))

    def post(self, request, *args, **kwargs):
        self.object = None

        multi_form_class = self.get_multi_form_class()
        multi_form = self.get_multi_form(multi_form_class)

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid() and multi_form.is_valid():
            return self.form_valid(form, multi_form)
        else:
            return self.form_invalid(form, multi_form)

    def form_invalid(self, form, multi_form):
        return self.render_to_response(self.get_context_data(form=form, multi_form=multi_form))

    def form_valid(self, form, multi_form):
        self.object = form.save()
        self.multi_objects = multi_form.save()

        return super(MultiFormMixin, self).form_valid(form)


class VersionsNewView(MultiFormMixin, RequiresPermissionMixin, ProjectNavbarMixin, CreateView):

    model = Version
    template_name = 'versions/new.html'

    form_class = NewVersionForm
    prefix = 'version'
    active_project_tab = 'versions'

    multi_form_class = NewVersionInnerFileFormset
    multi_prefix = 'file'
    multi_initial = {}

    permissions = ['project.manage', 'version.create', 'file.create']

    def get_project(self):
        return get_object_or_404(Project, name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])

    def get_multi_form_kwargs(self):
        kwargs = super(VersionsNewView, self).get_multi_form_kwargs()
        kwargs.update({
            'queryset': File.objects.none(),
            'project': self.get_project(),
        })
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(VersionsNewView, self).get_context_data(**kwargs)
        data.update({
            'proj': self.get_project()
        })
        return data

    def form_valid(self, form, multi_form):

        name = form.cleaned_data['name']

        if self.get_project().versions.filter(name=name).count():
            form.add_error(
                'name', 'That version name already exists in this project')
            return self.form_invalid(form, multi_form)

        self.object = form.save()

        self.multi_objects = multi_form.save(commit=False)
        for multi_object in self.multi_objects:
            multi_object.version = self.object
            multi_object.project = self.get_project()
            multi_object.save()

        return super(VersionsNewView, self).form_valid(form, multi_form)

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
    template_name = 'versions/detail.html'
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


class ChannelsListView(RequiresPermissionMixin, DetailView):
    model = Project
    slug_field = 'name'
    slug_url_kwarg = 'project'

    template_name = 'channels/manage.html'
    context_object_name = 'proj'

    def get_permissions(self, request, *args, **kwargs):
        if request.method.lower() == 'post':
            return ('project.manage', 'channel.create')
        return ('project.manage',)

    def get_queryset(self):
        return Project.objects.as_user(self.request.user).filter(namespace__name=self.kwargs['namespace'], name=self.kwargs['project'])

    def get_context_data(self, **kwargs):
        context = super(ChannelsListView, self).get_context_data(**kwargs)
        context['form'] = NewChannelForm(
            initial={'name': 'my awesome new channel'},
            used_colours=self.object.channel_set.values_list('hex', flat=True))
        context['active_project_tab'] = 'versions'
        return context

    def post(self, request, *args, **kwargs):
        self.object = project = self.get_object()
        form = NewChannelForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.project = project
            channel.save()
            form = NewChannelForm()
        return self.get(request, *args, **kwargs)


class DeleteChannelView(RequiresPermissionMixin, FormView):
    template_name = "channels/confirmdelete.html"
    form_class = ChannelDeleteForm
    permissions = ('project.manage', 'channel.delete',)

    def get_context_data(self, **kwargs):
        context = super(DeleteChannelView, self).get_context_data(**kwargs)
        context['proj'] = Project.objects.as_user(self.request.user).get(
            name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])
        context['channel'] = Channel.objects.get(
            pk=self.kwargs['channel'], project=context['proj'])
        context['active_project_tab'] = 'versions'
        return context

    def get_project(self):
        return get_object_or_404(
            Project.objects.as_user(self.request.user),
            name=self.kwargs['project'], namespace__name=self.kwargs['namespace'])

    def get_form(self, **kwargs):
        project = self.get_project()
        return ChannelDeleteForm(
            project,
            Channel.objects.get(pk=self.kwargs['channel'], project=project),
            **self.get_form_kwargs())

    def form_valid(self, form):
        project = self.get_project()
        channel = get_object_or_404(
            Channel, pk=self.kwargs['channel'], project=project)
        if form.cleaned_data['transfer_to'] == "DEL":
            channel.delete()
        else:
            versions_to_transfer = Version.objects.filter(channel=channel)
            new_channel = get_object_or_404(
                Channel,
                pk=form.cleaned_data['transfer_to'], project=project)
            versions_to_transfer.update(channel=new_channel)
            channel.delete()
        return redirect('project-channels', namespace=project.namespace.name, project=project.name)


class EditChannelView(RequiresPermissionMixin, FormView):
    template_name = "channels/manage.html"
    form_class = NewChannelForm
    permissions = ('project.manage', 'channel.edit',)

    def get_context_data(self, **kwargs):
        context = super(EditChannelView, self).get_context_data(**kwargs)
        context['proj'] = self.get_project()
        context['editing'] = True
        context['active_project_tab'] = 'versions'
        return context

    def get_project(self):
        return get_object_or_404(
            Project.objects.as_user(self.request.user), namespace__name=self.kwargs['namespace'], name=self.kwargs['project'])

    def get_form(self, **kwargs):
        project = self.get_project()
        channel = Channel.objects.get(
            pk=self.kwargs['channel'], project=project)
        return NewChannelForm(instance=channel,
                              used_colours=project.channel_set.values_list(
                                  'hex', flat=True),
                              **self.get_form_kwargs())

    def form_valid(self, form):
        project = self.get_project()
        channel = get_object_or_404(
            Channel, pk=self.kwargs['channel'], project=project)
        channel = form.save(commit=False)
        channel.project = project
        channel.save()
        return redirect('project-channels', namespace=project.namespace.name, project=project.name)
