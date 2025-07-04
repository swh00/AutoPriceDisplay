import tkinter as tk
import time
import os

def read_and_display():
    try:
        with open("display_text.txt", "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        text = ""
    # Text 위젯 업데이트
    text_widget.config(state='normal')
    text_widget.delete('1.0', 'end')
    text_widget.insert('1.0', text)
    text_widget.config(state='disabled')

    root.after(1000, read_and_display)

root = tk.Tk()
root.attributes('-fullscreen', True)
root.configure(bg='black')

text_widget = tk.Text(
    root,
    font=('NanumGothicCoding', 20),
    fg='white',
    bg='black',
    wrap='none'    # 자동 줄바꿈 끄기
)
text_widget.pack(fill='both', expand=True)
text_widget.config(state='disabled')

root.after(1000, read_and_display)
root.mainloop()

