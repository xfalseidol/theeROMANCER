from hotline_demo import run_hotline
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def on_slider_change(event):
    run_hotline_guiparam()


n_charts = 0
canvases = []

def run_hotline_guiparam():
    global n_charts
    n_charts = 0
    run_hotline(red_response_threshhold=red_threshold_slider.get(), blue_response_threshhold=blue_threshold_slider.get())

root = tk.Tk()
root.title("Hotline")

def my_show():
    global canvases, n_charts
    fig = plt.gcf()
    fig.set_size_inches(4, 3)
    if n_charts <= len(canvases):
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=n_charts//2, column=n_charts%2)
        canvases.append(canvas)
    else:
        canvases[n_charts].figure = fig
        canvases[n_charts].draw()
    n_charts += 1


plt.show = my_show

red_slider_label = ttk.Label(root, text="Red Response Threshold")
red_slider_label.pack()
red_threshold_slider = ttk.Scale(root, from_=0.0, to=1.0, orient="horizontal")
red_threshold_slider.pack()
red_threshold_slider.bind("<ButtonRelease-1>", on_slider_change)

blue_slider_label = ttk.Label(root, text="Blue Response Threshold")
blue_slider_label.pack()
blue_threshold_slider = ttk.Scale(root, from_=0.0, to=1.0, orient="horizontal")
blue_threshold_slider.pack()
blue_threshold_slider.bind("<ButtonRelease-1>", on_slider_change)

run_button = ttk.Button(root, text="Run", command=run_hotline_guiparam)
run_button.pack()

frame = ttk.Frame(root)
frame.pack()

root.mainloop()