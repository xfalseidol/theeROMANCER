from hotline_demo import run_hotline
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HotlineGUI:
    def __init__(self):
        self.n_charts = 0
        self.canvases = []
        self.root = tk.Tk()
        self.root.title("Hotline")

        red_slider_label = ttk.Label(self.root, text="Red Response Threshold")
        red_slider_label.pack()
        self.red_threshold_slider = ttk.Scale(self.root, from_=0.0, to=1.0, orient="horizontal")
        self.red_threshold_slider.pack()
        self.red_threshold_slider.bind("<ButtonRelease-1>", self.on_slider_change)

        blue_slider_label = ttk.Label(self.root, text="Blue Response Threshold")
        blue_slider_label.pack()
        self.blue_threshold_slider = ttk.Scale(self.root, from_=0.0, to=1.0, orient="horizontal")
        self.blue_threshold_slider.pack()
        self.blue_threshold_slider.bind("<ButtonRelease-1>", self.on_slider_change)

        self.run_button = ttk.Button(self.root, text="Run", command=self.run_hotline_guiparam)
        self.run_button.pack()

        self.frame = ttk.Frame(self.root)
        self.frame.pack()

    def on_slider_change(self, event):
        self.run_hotline_guiparam()

    def mainloop(self):
        self.root.mainloop()

    def run_hotline_guiparam(self):
        self.n_charts = 0
        run_hotline(red_response_threshhold=self.red_threshold_slider.get(), blue_response_threshhold=self.blue_threshold_slider.get())

    def hotline_show(self):
        fig = plt.gcf()
        fig.set_size_inches(4, 3)
        if self.n_charts <= len(self.canvases):
            canvas = FigureCanvasTkAgg(fig, master=self.frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=self.n_charts//2, column=self.n_charts%2)
            self.canvases.append(canvas)
        else:
            self.canvases[self.n_charts].figure = fig
            self.canvases[self.n_charts].draw()
        self.n_charts += 1


if __name__ == "__main__":
    hgui = HotlineGUI()
    def show_capture():
        hgui.hotline_show()
    plt.show = show_capture

    hgui.mainloop()