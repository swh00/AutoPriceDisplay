'''
analyzer/utils.py
Utility functions for the image search engine.
'''

import torch
import faiss
import clip
import os
from PIL import Image
import numpy as np
from pyzbar.pyzbar import decode
import cv2

# CLIP 모델 로딩
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# FAISS 인덱스 및 매핑
index = faiss.IndexFlatL2(512)  # 512차원 벡터
id_to_product = {}  # {faiss_index_position: product_id}

def add_embedding_to_index(product_id, embedding):
    """
    FAISS 인덱스에 임베딩 추가
    :param product_id: 상품 ID
    :param embedding: 상품 임베딩 (1, 512)
    """
    global index, id_to_product
    if product_id in id_to_product.values():
        print(f"[INFO] 이미 등록된 product_id: {product_id}, 생략됨.")
        return
    if embedding.shape != (1, 512):
        raise ValueError(f"Embedding shape mismatch: {embedding.shape}")
    index.add(embedding)
    id_to_product[index.ntotal - 1] = product_id


def find_nearest_product(embedding, k=1):
    """
    FAISS 인덱스에서 가장 가까운 상품 찾기
    :param embedding: 상품 임베딩 (1, 512)
    :param k: 반환할 가장 가까운 상품 수
    :return: 가장 가까운 상품 ID 리스트
    """
    _, indices = index.search(embedding, k)
    return [id_to_product.get(i) for i in indices[0]]

def save_faiss_index(path='faiss.index', map_path='faiss_map.npy'):
    """
    FAISS 인덱스와 매핑 저장
    :param path: FAISS 인덱스 저장 경로
    :param map_path: ID 매핑 저장 경로
    """
    faiss.write_index(index, path)
    np.save(map_path, id_to_product)

def load_faiss_index(path='faiss.index', map_path='faiss_map.npy'):
    """
    FAISS 인덱스와 매핑 로드
    :param path: FAISS 인덱스 로드 경로
    :param map_path: ID 매핑 로드 경로
    """
    global index, id_to_product
    if os.path.exists(path):
        index = faiss.read_index(path)
        print(f"FAISS 인덱스 로드됨: {path}")
    if os.path.exists(map_path):
        id_to_product = np.load(map_path, allow_pickle=True).item()
        print(f"FAISS ID 매핑 로드됨: {map_path}")

def embed_image(image_path):
    """
    이미지 파일을 임베딩 벡터로 변환
    :param image_path: 이미지 파일 경로
    :return: 임베딩 벡터 (1, 512)
    """
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model.encode_image(image).cpu().numpy()
    return embedding

def reset_faiss_index():
    """
    FAISS 인덱스 초기화
    """
    global index, id_to_product
    index = faiss.IndexFlatL2(512)
    id_to_product = {}
    print("FAISS 인덱스 초기화됨.")
    
def build_faiss_from_embeddings():
    """
    DB에 있는 모든 ProductEmbedding을 불러와
    FAISS index와 매핑을 재생성
    """
    from .models import ProductEmbedding

    global index, id_to_product
    index.reset()
    id_to_product.clear()

    for pe in ProductEmbedding.objects.all():
        embedding = np.frombuffer(pe.embedding, dtype=np.float32).reshape(1, -1)
        add_embedding_to_index(pe.product.id, embedding)


def clean_orphaned_ids():
    """
    DB에서 삭제된 Product ID를 FAISS 매핑에서 제거하고,
    전체 index 재생성
    """
    from .models import ProductEmbedding, Product

    print("[INFO] FAISS orphaned ID 정리 시작")

    # 존재하는 product_id만 필터링
    valid_product_ids = set(Product.objects.values_list("id", flat=True))

    reset_faiss_index()  # 전체 인덱스 초기화

    for pe in ProductEmbedding.objects.all():
        if pe.product.id in valid_product_ids:
            embedding = np.frombuffer(pe.embedding, dtype=np.float32).reshape(1, -1)
            add_embedding_to_index(pe.product.id, embedding)

    print("[INFO] 정리 완료: 유효 product 수 =", index.ntotal)
