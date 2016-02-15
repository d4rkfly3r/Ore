from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field, Hidden
from django import forms
from django.core.urlresolvers import reverse
from django.forms import modelformset_factory
from ore.projects.models import Channel
from ore.versions.models import Version, File


class NewVersionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(NewVersionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            Field('name'),
            Field('description', css_class="oredown"),
        )
        self.fields['channel'] = forms.ModelChoiceField(
            queryset=Channel.objects.filter(project_id=kwargs['instance'].project.id))

    class Meta:
        model = Version
        fields = ('name', 'description', 'channel')

        # def validate_unique(self):
        #     exclude = self._get_validation_exclusions()
        #     exclude.remove('version')
        #
        #     try:
        #         self.instance.validate_unique(exclude=exclude)
        #     except ValidationError as e:
        #         self._update_errors(e.message_dict)


class NewChannelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        used_colours = set(kwargs.pop('used_colours', set()))
        super(NewChannelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = "form-horizontal colour-form"
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        label = 'Create new channel' if not self.instance.id else 'Edit channel'
        if self.instance.id:
            used_colours.remove(self.instance.hex)
        self.helper.layout = Layout(
            Field('name', autocomplete='off'),
            Field('hex', css_class="colour-selector only-without-js"),
            Submit('submit', label, css_class="col-lg-offset-2")
        )
        self.fields['hex'].choices = [
            (hex, name) for (hex, name) in self.fields['hex'].choices if hex not in used_colours]

    class Meta:
        model = Channel
        fields = ('name', 'hex')

    COLOUR_CHOICES = (
        ('001F3F', 'Navy'),
        ('0074D9', 'Blue'),
        ('7FDBFF', 'Aqua'),
        ('39CCCC', 'Teal'),
        ('3D9970', 'Olive'),
        ('2ECC40', 'Green'),
        ('01FF70', 'Lime'),
        ('FFDC00', 'Yellow'),
        ('FF851B', 'Orange'),
        ('FF4136', 'Red'),
        ('85144B', 'Maroon'),
        ('F012BE', 'Fuchsia'),
        ('B10DC9', 'Purple'),
        ('111111', 'Black'),
        ('AAAAAA', 'Gray'),
        ('DDDDDD', 'Silver'),
    )

    hex = forms.ChoiceField(
        choices=COLOUR_CHOICES, required=True, label='Colour')


class ChannelDeleteForm(forms.Form):

    def __init__(self, project, current_channel, *args, **kwargs):
        super(ChannelDeleteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        get_out_of_here = reverse(
            'project-channels', kwargs={'namespace': project.namespace.name, 'project': project.name})
        self.helper.layout = Layout(
            'transfer_to',
            Submit(
                'submit', 'Delete it!', css_class='btn-danger col-lg-offset-2'),
            HTML(
                "<a href=\"{}\" class='btn'>Get me out of here!</a>".format(get_out_of_here))
        )
        channels = Channel.objects.filter(
            project=project).exclude(id=current_channel.id)
        choices = [('DEL', 'None, delete them.'), ] + \
            [(str(channel.id), channel.name) for channel in channels]
        self.fields['transfer_to'] = forms.ChoiceField(
            choices=choices, required=False)


class NewFileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        project = None
        if 'project' in kwargs:
            project = kwargs.pop('project')
        super(NewFileForm, self).__init__(*args, **kwargs)
        if project:
            self.project = project
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Field('file'),
        )
        if kwargs['prefix'] == 'file-0':
            self.fields['file'].label = 'Primary file'
        else:
            self.fields['file'].label = 'Additional file'

    def clean(self):
        cleaned_data = super().clean()
        if self.empty_permitted and not self.has_changed():
            cleaned_data['project'] = self.project if 'file' in cleaned_data else None
        return cleaned_data

    class Meta:
        model = File
        fields = ('file', 'project')
        widgets = {'project': forms.HiddenInput()}

BaseNewVersionInnerFileFormset = modelformset_factory(
    File, form=NewFileForm, max_num=5, validate_max=True)


class NewVersionInnerFileFormset(BaseNewVersionInnerFileFormset):

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project')
        super(NewVersionInnerFileFormset, self).__init__(*args, **kwargs)
        self.form_kwargs['project'] = project
        #self.form.initial['project'] = self.form.project
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            #Fieldset('File', 'name', 'file')
            Field('file'),
        )
