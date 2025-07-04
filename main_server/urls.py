from django.urls import path
from .views import analyze_display, login, reload_faiss_index, register_display

app_name = "analyzer"

urlpatterns = [
    path('analyze/', analyze_display, name='analyze_display'),
    path('login/', login, name='login'),
    path('reload-faiss/', reload_faiss_index, name='reload_faiss_index'),
    path('register_display', register_display, name='register_display'),
]
