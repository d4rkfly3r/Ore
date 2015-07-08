from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, HTML, ButtonHolder, Field, Hidden
from django import forms
from django.core.exceptions import ValidationError
from ore.versions.models import Version, File, Channel


class NewVersionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(NewVersionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            'name',
            'channel',
            'description',
        )

    class Meta:
        model = Version
        fields = ('name', 'channel', 'description')


class NewFileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(NewFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'file',
            Submit('submit', 'Upload')
        )

    class Meta:
        model = File
        fields = ('file',)


class VersionEditForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'channel',
            'description',
            Submit('submit', 'Edit'),
        )

    class Meta:
        model = Version
        fields = ('channel', 'description',)


class VersionRenameForm(forms.ModelForm):

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.helper = FormHelper(self)
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

    def clean_name(self):
        new_name = self.cleaned_data['name']
        old_name = self.instance.name
        if new_name == old_name:
            return old_name

        versions = self.project.versions.all()
        for version in versions:
            if version.name.lower() == new_name.lower():
                raise ValidationError("A version by that name already exists!")

        return new_name

    class Meta:
        model = Version
        fields = ('name',)


class ChannelForm(forms.ModelForm):

    def clean_name(self):
        new_name = self.cleaned_data['name']
        old_name = self.instance.name
        if new_name == old_name:
            return old_name

        channels = self.project.get_channels()
        for ch in channels:
            if ch.name.lower() == new_name.lower():
                raise ValidationError("A channel by that name already exists!")

        return new_name

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.project = project

        instance = kwargs.get('instance')

        self.fields['colour'].widget = forms.TextInput(
            attrs=dict(type='color'))

        btn = Submit('submit', 'Update', css_class='btn-default') if instance else Submit(
            'submit', 'Create', css_class='btn-success')

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Hidden('action', 'create'),
            'name',
            Field('colour', type='color'),
            btn
        )

    class Meta:
        model = Channel
        fields = ('name', 'colour',)
