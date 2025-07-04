# analyzer/yolo_utils.py

from ultralytics import YOLO
from PIL import Image, ImageDraw
import os
import numpy as np
from datetime import datetime

model = YOLO("yolo11x.pt")  # pretrained YOLO 모델 로딩

def iou(box1, box2):
    """ 두 box 사이의 IoU (Intersection over Union) 계산 """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    if inter_area == 0:
        return 0.0
    
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union_area = box1_area + box2_area - inter_area
    return inter_area / union_area

def non_max_suppression(boxes, confidences, iou_thresh=0.4):
    """ 겹치는 박스 제거 (NMS 수행) """
    indices = np.argsort(confidences)[::-1]
    keep = []

    while len(indices) > 0:
        current = indices[0]
        keep.append(current)
        current_box = boxes[current]
        
        remaining = []
        for i in indices[1:]:
            if iou(current_box, boxes[i]) < iou_thresh:
                remaining.append(i)
        indices = remaining

    return [boxes[i] for i in keep]

# 상품 객체들을 감지하고 bounding box 정보 반환
def detect_objects(image_path, conf_threshold=0.05, iou_threshold=0.4):
    results = model(image_path, conf=conf_threshold)
    boxes_tensor = results[0].boxes.xyxy.cpu().numpy()  # (N, 4)
    confidences = results[0].boxes.conf.cpu().numpy()  # (N,)

    # confidence threshold 적용
    filtered = [(box, conf) for box, conf in zip(boxes_tensor, confidences) if conf >= conf_threshold]
    if not filtered:
        return []

    boxes, confidences = zip(*filtered)
    boxes = np.array(boxes)
    confidences = np.array(confidences)

    filtered_boxes = non_max_suppression(boxes, confidences, iou_thresh=iou_threshold)
    return filtered_boxes

# 감지된 박스를 이용해 상품 이미지 잘라 저장
def crop_image(image_path, boxes, save_dir):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    full_save_dir = os.path.join(save_dir, timestamp)
    os.makedirs(full_save_dir, exist_ok=True)

    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    cropped_paths = []

    for i, (x1, y1, x2, y2) in enumerate(boxes):
        cropped = image.crop((x1, y1, x2, y2))
        save_path = os.path.join(full_save_dir, f"crop_{i}.jpg")
        cropped.save(save_path)
        cropped_paths.append(save_path)

    for (x1, y1, x2, y2) in boxes:
        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)

    result_path = os.path.join(full_save_dir, f"result.jpg")
    image.save(result_path)
    return cropped_paths

