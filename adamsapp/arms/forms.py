from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML


class AddDataForm(forms.Form):
    left_file = forms.FileField(required=False, label="Data File Left")
    right_file = forms.FileField(required=False, label="Data File Right")
    notes = forms.CharField(required=False, widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super(AddDataForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-6'
        self.helper.form_method = 'post'
        self.helper.form_id = 'id-form'
        self.helper.add_input(Submit('submit', 'Add'))


class RemoveItemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        return_name = kwargs.pop('return_name')

        super(RemoveItemForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
                Submit('submit', "Yes, I'm sure", css_class='btn-danger'),
                HTML('<a class="btn btn-default" href="' + return_name + '">No, take me back</a>'),
        )