from django import forms
from .models import Work, Category


class WorkCreateForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'category-checkbox-group'}),
        required=False,
        label="Категории"
    )

    class Meta:
        model = Work
        fields = ['title', 'description', 'categories', 'file', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название работы'}),
            'description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Опишите вашу научную работу'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0 - бесплатно'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['file'].widget.attrs.update({'class': 'form-control'})
        self.fields['price'].widget.attrs.update({'class': 'form-control'})

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title.strip()) < 5:
            raise forms.ValidationError('Название должно содержать минимум 5 символов')
        return title

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной')
        if price > 10000:
            raise forms.ValidationError('Максимальная цена - 10 000 ₽')
        return price

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        file = cleaned_data.get('file')
        if price and price > 0 and not file:
            raise forms.ValidationError('Для платной работы необходимо загрузить файл')
        return cleaned_data


class WorkFilterForm(forms.Form):
    """Форма для фильтрации работ"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию, описанию или автору...'
        })
    )
    price = forms.ChoiceField(
        required=False,
        choices=[('', 'Все'), ('free', 'Бесплатные'), ('paid', 'Платные')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'category-filter-group'})
    )

class WorkModerationForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = ['moderation_status', 'moderation_comment']
        widgets = {
            'moderation_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }