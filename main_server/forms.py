# analyzer/forms.py

from django import forms
from .models import Product

# 관리자 페이지에서 제품을 추가/수정할 때 사용할 폼
class ProductAdminForm(forms.ModelForm):
    image_upload = forms.ImageField(required=False)

    class Meta:
        model = Product
        fields = ['name', 'price', 'event']  # image_path는 자동 설정됨
