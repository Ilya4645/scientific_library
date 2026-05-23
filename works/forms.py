from django import forms
from .models import Work


class WorkCreateForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = ['title', 'description', 'file', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

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