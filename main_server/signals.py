from django.db.models.signals import post_save
from django.dispatch import receiver
from analyzer.models import Product, Display, DisplayTextOverlay # Assuming these are your models
import requests
from wcwidth import wcwidth
from decimal import Decimal


# 인증 헤더
headers = {'Authorization': '123sdaf12124'} 


BLOCK_WIDTH = 20 #문자 수 (한칸)
Display_WIDTH = 30.0  # cm


def char_width(ch: str) -> int:
    """한글(U+AC00~U+D7A3)=2, 그 외=1로 폭 계산."""
    return 2 if '\uAC00' <= ch <= '\uD7A3' else 1

def text_width(s: str) -> int:
    """문자열 전체 폭."""
    return sum(char_width(ch) for ch in s)

def generate_display_lines_wcwidth(
    overlays,
    CHARS_PER_LINE: int = 147,
    BLOCK_WIDTH: int    = 20,
    DISPLAY_WIDTH: float= 30.0
) -> str:
    """
    overlays: DisplayTextOverlay 쿼리셋 또는 리스트
      각 item에 .text="name,price,promo", .x(cm)
    반환: 3줄(\n)로 합친 문자열. 
    wcwidth를 써서 '한글=2셀, 영문/숫자=1셀' 을 정확히 반영합니다.
    """# 1) 셀 단위 버퍼: 공백을 CHARS_PER_LINE 개 만큼 준비
    line1 = [" "] * CHARS_PER_LINE
    line2 = [" "] * CHARS_PER_LINE
    line3 = [" "] * CHARS_PER_LINE

    # 새로운: 점유 상태 추적용 버퍼
    occupied1 = [False] * CHARS_PER_LINE
    occupied2 = [False] * CHARS_PER_LINE
    occupied3 = [False] * CHARS_PER_LINE

    def can_insert(buf_occupied: list, start_cell: int, text: str) -> bool:
        """이 셀 영역에 텍스트를 넣을 수 있는지 확인"""
        pos = start_cell
        for ch in text:
            w = max(wcwidth(ch), 1)
            if pos + w > CHARS_PER_LINE:
                return False
            for i in range(w):
                if buf_occupied[pos + i]:
                    return False
            pos += w
        return True

    def insert_into_buffer(buf: list, buf_occupied: list, start_cell: int, text: str):
        """buf[start_cell:]에 텍스트 삽입, occupied도 업데이트"""
        pos = start_cell
        for ch in text:
            w = max(wcwidth(ch), 1)
            buf[pos] = ch
            buf_occupied[pos] = True
            if w == 2 and pos + 1 < CHARS_PER_LINE:
                buf[pos + 1] = ""
                buf_occupied[pos + 1] = True
            pos += w
            
    DISPLAY_WIDTH = Decimal(str(DISPLAY_WIDTH))
    
    for overlay in overlays:
        try:
            name, price, promo = map(str.strip, overlay.text.split(","))
        except ValueError:
            continue
    
        base = int(round(overlay.x / DISPLAY_WIDTH * CHARS_PER_LINE))
        block_start = base - BLOCK_WIDTH // 2
        block_start = max(0, min(block_start, CHARS_PER_LINE - BLOCK_WIDTH))
    
        text_triples = [
                (line1, occupied1, name),
            (line2, occupied2, price),
            (line3, occupied3, promo)
        ]
    
        # 👇 겹치는 텍스트가 하나라도 있으면 전체 스킵
        conflict = False
        for _, buf_occ, text in text_triples:
            text_w = sum(max(wcwidth(ch), 1) for ch in text)
            start_cell = block_start + (BLOCK_WIDTH - text_w) // 2
            if not can_insert(buf_occ, start_cell, text):
                conflict = True
                break
    
        if conflict:
   #         print(f"[SKIPPED] Text '{overlay.text}' at x={overlay.x} overlapped existing content.")
            continue
    
        # 👇 전부 삽입
        for buf, buf_occ, text in text_triples:
            text_w = sum(max(wcwidth(ch), 1) for ch in text)
            start_cell = block_start + (BLOCK_WIDTH - text_w) // 2
            insert_into_buffer(buf, buf_occ, start_cell, text)

    out1 = "".join(ch for ch in line1 if ch != "")
    out2 = "".join(ch for ch in line2 if ch != "")
    out3 = "".join(ch for ch in line3 if ch != "")
    return "\n".join((out1.rstrip(), out2.rstrip(), out3.rstrip()))

@receiver(post_save, sender=DisplayTextOverlay)
def send_texts_to_display(sender, instance, created, **kwargs):
    overlays = DisplayTextOverlay.objects.filter(display_id=instance.display_id).order_by('x')
    display = Display.objects.get(display_id=instance.display_id)
    target_url = display.display_url.rstrip('/') + "/display"
    
    CHARS_PER_LINE = display.CPL
    
    text_blocks = generate_display_lines_wcwidth(overlays, CHARS_PER_LINE=CHARS_PER_LINE)
    full_text = ""
    for block in text_blocks:
        full_text += block

    data = {
        'display_id': instance.display_id,
        'text': full_text
    }
    
    
    print(f"Target URL: {target_url}\nText to display:\n{full_text}")
    
    try:
        response = requests.post(target_url, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        print(f"Signal: Successfully sent data to display. Status: {response.status_code}")
    except requests.RequestException as e:
        print(f"[POST ERROR] {e}")
