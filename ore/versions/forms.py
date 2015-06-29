from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, HTML, ButtonHolder
from django import forms
from django.forms import modelformset_factory
from ore.versions.models import Version, File


class NewVersionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(NewVersionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            'name',
            'description',
        )

    class Meta:
        model = Version
        fields = ('name', 'description')


class NewFileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(NewFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'file'
        )

    class Meta:
        model = File
        fields = ('file',)


class VersionDescriptionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'description',
            Submit('submit', 'Change description'),
        )

    class Meta:
        model = Version
        fields = ('description',)


class VersionRenameForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    class Meta:
        model = Version
        fields = ('name',)
