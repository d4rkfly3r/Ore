from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset
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
