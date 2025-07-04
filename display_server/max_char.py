import tkinter as tk
from tkinter import font

root = tk.Tk()
root.attributes('-fullscreen', True)

# 사용할 폰트 정의
display_font = font.Font(family='NanumGothicCoding', size=20)

# 전체 화면 너비 (픽셀 단위)
screen_width_px = root.winfo_screenwidth()

# 폰트 기준 한 글자의 너비 (픽셀 단위)
char_width_px = display_font.measure("0")  # 한글 한 글자의 픽셀 너비

# 가능한 문자 수
chars_per_line = screen_width_px // char_width_px

print(f"스크린 픽셀 너비: {screen_width_px}")
print(f"문자 하나당 너비: {char_width_px}")
print(f"한 줄에 출력 가능한 문자 수: {chars_per_line}")

