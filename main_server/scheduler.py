# analyzer/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from .models import DetectedProduct, DisplayTextOverlay, Product
from django.utils import timezone
import atexit
from django.db import transaction

# 스케줄러를 사용하여 매월 1일 자정에 가격 정보를 갱신하는 함수
def update_display_texts(where="Scheduler"):
    
    print(f"[{where}] 가격 정보 갱신 시작")
    detected_products = DetectedProduct.objects.select_related('product').all()

    if not detected_products.exists():
        print(f"[{where}] 갱신할 DetectedProduct가 없습니다.")
        return
    
    display_ids_to_update = detected_products.values_list('display_id', flat=True).distinct()
    overlays_to_create = []

    for dp in detected_products:
        product = dp.product 
        event_text = f"({product.event})" if product.event else "(행사X)"
        text = f"{product.name},{product.price},{event_text}"

        overlays_to_create.append(
            DisplayTextOverlay(
                product=dp.product,
                display_id=dp.display_id,
                x=dp.x_center,
                text=text
            )
        )

    with transaction.atomic():
        print(f"[{where}] 기존 DisplayTextOverlay 삭제 (대상 ID: {list(display_ids_to_update)})")
        DisplayTextOverlay.objects.filter(display_id__in=display_ids_to_update).delete() 
        
        print(f"[{where}] {len(overlays_to_create)}개 DisplayTextOverlay bulk_create 시작")
        DisplayTextOverlay.objects.bulk_create(overlays_to_create)

    print(f"{len(overlays_to_create)}개의 DisplayTextOverlay가 동기화되었습니다.")
    print(f"[{where}] 갱신 완료")

# 스케줄러 시작 함수
def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_display_texts, 'cron', day=1, hour=0, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())