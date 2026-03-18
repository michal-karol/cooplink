from django import forms

from .models import Category, Link


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ["title", "url", "description", "category"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all shared categories in alphabetical order.
        self.fields["category"].queryset = Category.objects.all().order_by("name")
        # Category is optional
        self.fields["category"].required = False
        self.fields["category"].empty_label = "No category"

    def clean_title(self):
        # Strip spaces from the start or end of the title
        return self.cleaned_data["title"].strip()

    def clean_description(self):
        # blank descriptions are ok, but cleaned up if any text is entered
        description = self.cleaned_data["description"]
        return description.strip() if description else ""