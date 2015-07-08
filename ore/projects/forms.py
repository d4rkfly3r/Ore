from ore.accounts.models import OreUser
from ore.core.models import Namespace, Organization
from ore.core.regexs import EXTENDED_NAME_REGEX
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, ButtonHolder, Fieldset, HTML
from django import forms
from django.core import validators
from django.core.urlresolvers import reverse
from django.db.models import Q
from ore.projects.models import Project


class ProjectForm(forms.ModelForm):

    namespace = forms.ModelChoiceField(
        label='Owner User / Organization', queryset=None, empty_label=None)
    description = forms.CharField(
        label='Tagline (optional)', widget=forms.TextInput(), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ProjectForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Create project'))

        namespace = self.fields['namespace']
        namespace.queryset = Namespace.objects.select_subclasses(Organization, OreUser).filter(
            Q(oreuser=user) |
            (Q(organization__teams__users=user) & (Q(organization__teams__is_owner_team=True) | Q(
                organization__teams__permissions__slug='project.create')))
        )

        namespace.initial = user.id

    class Meta:
        model = Project
        fields = ['name', 'namespace', 'description']


class ProjectDescriptionForm(forms.ModelForm):

    description = forms.CharField(
        label='Tagline (optional)', widget=forms.TextInput(), required=False)

    def __init__(self, *args, **kwargs):
        namespace = kwargs.pop('namespace')
        project = kwargs.pop('project')
        super(ProjectDescriptionForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.form_class = 'form-horizontal project-description-form'
        self.helper.form_action = reverse('repo-projects-describe',
                                           kwargs=dict(namespace=namespace, project=project))

        self.helper.layout = Layout(
            'description',
            Div(
                ButtonHolder(
                    Submit(
                        'submit', 'Change tagline', css_class='btn-default'),
                    css_class='col-md-offset-3 col-md-9'
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

        self.helper.form_action = reverse('repo-projects-rename',
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
