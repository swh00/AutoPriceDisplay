#analyzer/apps.py

from django.apps import AppConfig
from django.conf import settings

# 스케줄러를 사용하기 위한 설정
class AnalyzerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analyzer'

    def ready(self):
        from analyzer.utils import load_faiss_index, build_faiss_from_embeddings
        import analyzer.scheduler as scheduler
        import analyzer.signals

        if settings.RUNNING_MIGRATIONS:
            return 
        # FAISS 인덱스 로딩 시도
        if not load_faiss_index():
            # 디스크에 없을 경우 DB에서 다시 구축
            build_faiss_from_embeddings()

        scheduler.start()

