from ore.accounts.models import OreUser
from ore.core.models import Namespace, Organization
from ore.core.regexs import EXTENDED_NAME_REGEX
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, ButtonHolder, Fieldset, HTML, Field
from django import forms
from django.core import validators
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.html import conditional_escape, format_html, html_safe
from django.utils.safestring import mark_safe
from ore.projects.models import Project, Page


class NamespaceSelectWidget(forms.Select):

    def render_option(self, selected_choices, option_value, option_label):
        icon = option_label.avatar
        option_label = option_label.name
        addl_attrs = format_html('data-avatar="{}" ', icon)
        sup = super(NamespaceSelectWidget, self).render_option(
            selected_choices, option_value, option_label)
        assert sup[0:8] == '<option '
        sup = sup[0:8] + addl_attrs + sup[8:]
        return sup


class NamespaceSelectField(forms.ModelChoiceField):
    widget = NamespaceSelectWidget

    def label_from_instance(self, obj):
        return obj


class ProjectForm(forms.ModelForm):

    namespace = NamespaceSelectField(
        label='Owner User / Organization', queryset=None, empty_label=None)
    description = forms.CharField(
        label='Tagline (optional)', widget=forms.TextInput(), required=False, help_text=Project._meta.get_field('description').help_text)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ProjectForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Create project'))

        namespace = self.fields['namespace']
        namespace.queryset = Namespace.objects.as_user(user).select_subclasses(Organization, OreUser).filter(
            Q(oreuser=user) |
            (Q(organization__teams__users=user) & (Q(organization__teams__is_owner_team=True) | Q(
                organization__teams__permissions__slug='org.project.create')))
        ).order_by('oreuser__id', 'organization__name')
        namespace.initial = user.id

    class Meta:
        model = Project
        fields = ['name', 'namespace', 'description']


class ProjectDescriptionForm(forms.ModelForm):

    description = forms.CharField(
        label='Tagline (optional)', widget=forms.TextInput(), required=False, help_text=Project._meta.get_field('description').help_text)

    def __init__(self, *args, **kwargs):
        namespace = kwargs.pop('namespace')
        project = kwargs.pop('project')
        super(ProjectDescriptionForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-10'
        self.helper.form_class = 'form-horizontal project-description-form'
        self.helper._form_action = reverse('projects-describe',
                                           kwargs=dict(namespace=namespace, project=project))

        self.helper.layout = Layout(
            'description',
            Div(
                ButtonHolder(
                    Submit(
                        'submit', 'Change tagline', css_class='btn-default'),
                    css_class='col-md-offset-2 col-md-10'
                ),
                css_class='form-group',
            ),
            Div(
                css_class='clearfix'
            )
        )

    class Meta:
        model = Project
        fields = ['description']


class ProjectRenameForm(forms.ModelForm):

    name = forms.CharField(max_length=32,
                           validators=[
                               validators.RegexValidator(
                                   EXTENDED_NAME_REGEX, 'Enter a valid project name.', 'invalid')
                           ])

    def __init__(self, *args, **kwargs):
        namespace = kwargs.pop('namespace')
        project = kwargs.pop('project')
        super(ProjectRenameForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper._form_action = reverse('projects-rename',
                                           kwargs=dict(namespace=namespace, project=project))

        self.helper.layout = Layout(
            Div(
                Fieldset('',
                         HTML('''
                    <p>Are you sure you wish to rename this project?</p>
                     <p>While this operation is reversible, no redirects of any kind are set up and former links to your project may not work as expected.</p>
                '''),
                         'name',
                         ),
                css_class='modal-body'
            ),
            ButtonHolder(
                Submit('submit', 'Rename', css_class='btn-warning'),
                css_class='modal-footer'
            )
        )

    class Meta:
        model = Project
        fields = ['name']


class PageEditForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PageEditForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', readonly=self.instance.slug == 'home'),
            Field('content', css_class='oredown'),
            Submit('submit', 'Save'),
        )

    def clean_title(self):
        if self.instance.slug == 'home':
            return self.instance.title
        return self.cleaned_data['title']

    class Meta:
        model = Page
        fields = ['title', 'content']
