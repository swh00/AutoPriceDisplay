# analyzer/admin.py

from django.contrib import admin, messages
from django.urls import path, reverse 
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from .models import Product, ProductEmbedding, Display, DetectedProduct, DisplayTextOverlay
from .forms import ProductAdminForm
from .utils import embed_image, add_embedding_to_index, clean_orphaned_ids, save_faiss_index
from .scheduler import update_display_texts
import os

MEDIA_ROOT = 'media'

# 관리자 페이지에서 DisplayTextOverlay 모델을 표시하기 위한 커스텀 함수
@admin.register(DetectedProduct)
class DetectedProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'display_id', 'x_center')
    change_list_template = "admin/analyzer/detectedproduct_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("regenerate_display_texts/", self.admin_site.admin_view(self.run_update), name="regenerate_display_texts"),
        ]
        return custom_urls + urls

    def run_update(self, request):
        update_display_texts("admin")
        self.message_user(request, "가격 정보가 수동으로 갱신되었습니다.", level=messages.SUCCESS)
        return HttpResponseRedirect("../")

# 관리자 페이지에서 Product 모델을 표시하기 위한 커스텀 함수
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'price', 'event', 'image_path')
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        uploaded_file = form.cleaned_data.get('image_upload')
        if uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[1]
            filename = f"{obj.name}{ext}"
            save_path = os.path.join(MEDIA_ROOT, 'products', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            obj.image_path = f"products/{filename}"

        super().save_model(request, obj, form, change)

        embedding = embed_image(os.path.join(MEDIA_ROOT, obj.image_path))
        ProductEmbedding.objects.update_or_create(
            product=obj,
            defaults={"embedding": embedding.tobytes()}
        )
        add_embedding_to_index(obj.id, embedding)


# 관리자 페이지에서 Display 모델을 표시하기 위한 커스텀 함수
@admin.register(Display)
class DisplayAdmin(admin.ModelAdmin):
    list_display = ('display_id', 'display_url', 'width', 'CPL')
    search_fields = ('display_id',)
    
# 관리자 페이지에서 Display 모델의 display_url을 클릭할 수 있도록 커스터마이징
@admin.register(ProductEmbedding)
class ProductEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['product', 'created_at']
    actions = ['clean_faiss_index']

    def clean_faiss_index(self, request, queryset):
        clean_orphaned_ids()
        save_faiss_index()
        self.message_user(request, "[FAISS] 정리 및 저장 완료!", level=messages.SUCCESS)

    clean_faiss_index.short_description = "💡 FAISS 정리하기 (삭제된 Product 제거)"
    

admin.site.site_header = "Auto Labels 관리자"
admin.site.index_title = "관리 도구"
admin.site.site_title = "Auto Labels 관리"
