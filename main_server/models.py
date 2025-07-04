from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 상품 정보보
class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.PositiveIntegerField()
    event = models.CharField(max_length=50, blank=True)
    image_path = models.CharField(max_length=255)
    
    image_upload = None

# 디스플레이 정보보
class Display(models.Model):
    display_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,   # <- 기존 row에 NULL 허용
        blank=True,  # <- admin 페이지에서 빈 값 허용
        help_text="식별용 ID (예: 00001)"
    )
    width = models.DecimalField(max_digits=6, decimal_places=2)
    display_url = models.URLField(default='https://example.com')
    CPL = models.IntegerField(default=174, help_text="Characters Per Line")
    def __str__(self):
        return self.display_id if self.display_id else f"Display #{self.id}"
    
# 상품 임베딩 정보
class ProductEmbedding(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    embedding = models.BinaryField()
    created_at = models.DateTimeField(default=timezone.now)

# 상품이 디스플레이에 감지된 정보
class DetectedProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    display_id = models.CharField(max_length=20)
    x_center = models.DecimalField(max_digits=6, decimal_places=2)

# 디스플레이에 표시될 텍스트 오버레이 정보
class DisplayTextOverlay(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    display_id = models.CharField(max_length=20)
    x = models.DecimalField(max_digits=6, decimal_places=2)
    text = models.CharField(max_length=100)
