# Python Standard Library
import os
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Django REST Framework
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

# Third-party
from PIL import Image
import numpy as np
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Local app imports
from .models import ProductEmbedding, Display
from .utils import add_embedding_to_index
from analyzer.models import *
from analyzer.utils import *

# 공유키
SHARED_KEY = b'\x9f\x1c=&\xa6\xdf}\x8b$\x1c4\x85]\xe2\xc1\xa3\xd2\xb7\xe4\xf9c\x19\x114\xf6`\xaa\x84l\nMp'

with open('shared_key.key', 'rb') as f:
    SHARED_KEY = f.read()

# 데이터 복호화 함수 - 디스플레이 서버에서 받은 암호화된 데이터를 복호화하는 함수
def decrypt_data(encrypted_data: bytes) -> dict:
    aesgcm = AESGCM(SHARED_KEY)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(decrypted.decode('utf-8'))

# 데이터 암호화 함수 - 디스플레이 서버에 보낼 때 사용
@csrf_exempt
def register_display(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            encrypted_data = bytes.fromhex(data['encrypted_data'])  # ✅ 수정됨

            # 복호화
            decrypted_json = decrypt_data(encrypted_data)
            print(decrypted_json)
            
            display_id = decrypted_json.get('device_id')
            display_url = decrypted_json.get('display_url')  
            width = decrypted_json.get('width') 
            chars_per_line = decrypted_json.get('chars_per_line')
            
            if not display_id or not display_url:
                return JsonResponse({'error': 'Missing device_id or display_url'}, status=400)

            display, created = Display.objects.update_or_create(
                display_id=display_id,
                defaults={
                    'display_url': display_url,
                    'width':width,
                    'CPL':chars_per_line
                    }
            )

            return JsonResponse({'status': 'Display registered', 'display_id': display.display_id})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# 로그인 API - 사용자 인증 및 토큰 발급
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    else:
        return Response({'error': 'Invalid credentials'}, status=400)


# 디스플레이 분석 API - 이미지 업로드 및 분석
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_display(request):
    display_id = request.data.get("display_id")
    image = request.FILES["image"]
    ext = os.path.splitext(image.name)[-1]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}{ext}"
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    upload_path = os.path.join(upload_dir, filename)

    with open(upload_path, "wb+") as f:
        for chunk in image.chunks():
            f.write(chunk)

    if not display_id:
        display_id = "00001"

    from .yolo_utils import detect_objects, crop_image
    from .utils import embed_image, find_nearest_product

    DetectedProduct.objects.filter(display_id=display_id).delete()
    DisplayTextOverlay.objects.filter(display_id=display_id).delete()

    boxes = detect_objects(upload_path)
    cropped_paths = crop_image(upload_path, boxes, save_dir="media/crops")
    image_pil = Image.open(upload_path)
    image_width = image_pil.width
    display_width = Display.objects.get(display_id=display_id).width

    potential_overlays = []

    for path, box in zip(cropped_paths, boxes):
        embedding = embed_image(path)
        product_id = find_nearest_product(embedding)[0]

        x_center = (box[0] + box[2]) / 2
        x_center_d = Decimal(str(x_center))
        image_width_d = Decimal(str(image_width))
        display_width_d = Decimal(str(display_width))

        normalized_x = (x_center_d / image_width_d) * display_width_d
        normalized_x = normalized_x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        product = Product.objects.get(id=product_id)
        event_text = f"({product.event})" if product.event else "(행사X)"
        text = f"{product.name},{product.price},{event_text}"

        potential_overlays.append({
            'product_id': product_id,
            'normalized_x': normalized_x,
            'text': text,
            'product': product,
            'display_id': display_id
        })

    # x좌표 기준으로 정렬
    potential_overlays.sort(key=lambda item: item['normalized_x'])

    overlays_to_create = []
    detected_to_create = []
    last_x_added = None
    min_distance = Decimal('3.00')  # 최소 간격 설정 (필요에 따라 조정)

    for item in potential_overlays:
        current_x = item['normalized_x']
        text = item['text']

        # 마지막으로 추가된 항목과 거리 확인
        if last_x_added is None or (current_x - last_x_added) >= min_distance:
            detected_to_create.append(
                DetectedProduct(
                    product_id=item['product_id'],
                    display_id=item['display_id'],
                    x_center=current_x
                )
            )
            overlays_to_create.append(
                DisplayTextOverlay(
                    product=item['product'],
                    display_id=item['display_id'],
                    x=current_x,
                    text=text
                )
            )
            last_x_added = current_x  # 마지막 x좌표 업데이트
            print(f"In VIEWS - [ADDING] Text '{text}' at x={current_x}.")
        else:
            print(f"In VIEWS - [SKIPPED] Text '{text}' at x={current_x} overlapped with x={last_x_added}.")

    # 필터링된 항목들 DB에 저장
    DetectedProduct.objects.bulk_create(detected_to_create)

    if overlays_to_create:
        DisplayTextOverlay.objects.bulk_create(overlays_to_create[:-1])
        overlays_to_create[-1].save()

    existing = DisplayTextOverlay.objects.filter(display_id=display_id)
    return Response({"status": "analyzed", "detected": len(overlays_to_create)})


# 관리자 페이지에서 FAISS 인덱스 재생성
@staff_member_required
@require_POST
def reload_faiss_index(request):
    from .utils import reset_faiss_index
    reset_faiss_index()

    for pe in ProductEmbedding.objects.all():
        embedding = np.frombuffer(pe.embedding, dtype=np.float32).reshape(1, -1)
        add_embedding_to_index(pe.product.id, embedding)

    messages.success(request, "FAISS 인덱스를 재생성했습니다.")
    return redirect('/admin/')


def is_admin(user):
    return user.is_staff or user.is_superuser

# 관리자 페이지에서 보호된 미디어 파일 접근
@staff_member_required
def protected_media(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(full_path):
        return FileResponse(open(full_path, 'rb'))
    else:
        raise Http404("File not found")
