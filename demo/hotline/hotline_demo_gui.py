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
        self.sliders = {}
        self.slidervalues = {}
        self.slider_frame = tk.Frame(self.root)
        self.slider_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=10)

        self.create_slider("Red Response Threshold", "red_response_threshhold", 0.0, 1.0, 0.001, 0, 0)
        self.create_slider("Blue Initial PBF", "red_initial_pbf", 0.0, 100.0, 0.001, 0, 1)
        self.create_slider("Red Max PBF", "red_max_pbf", 0.0, 1.0, 1.0, 0, 2)
        self.create_slider("Red PBF Halflife", "red_pbf_halflife", 0.0, 100000.0, 100000, 0, 3)

        self.create_slider("Blue Response Threshold", "blue_response_threshhold", 0.0, 1.0, 0.001, 1, 0)
        self.create_slider("Blue Initial PBF", "blue_initial_pbf", 0.0, 100.0, 0.001, 1, 1)
        self.create_slider("Blue Max PBF", "blue_max_pbf", 0.0, 1.0, 1.0, 1, 2)
        self.create_slider("Blue PBF Halflife", "blue_pbf_halflife", 0.0, 100000.0, 100000, 1, 3)
        #
        # self.run_button = ttk.Button(self.root, text="Run", command=self.run_hotline_guiparam)
        # self.run_button.pack()

        self.chartframe = ttk.Frame(self.root)
        self.chartframe.pack()

        def show_capture():
            self.hotline_show()
        plt.show = show_capture
        self.run_hotline_guiparam()

    def create_slider(self, sliderlabel, slidername, slidermin, slidermax, sliderdefault, grid_x, grid_y):
        slider_label = ttk.Label(self.slider_frame, text=sliderlabel)
        slider_label.grid(row=grid_x, column=3*grid_y, padx=5, pady=5, sticky="w")
        slider = ttk.Scale(self.slider_frame, from_=slidermin, to=slidermax, orient="horizontal")
        slider.set(sliderdefault)
        slider.grid(row=grid_x, column=3*grid_y+1, padx=5, pady=5, sticky="ew")
        slider.bind("<ButtonRelease-1>", self.on_slider_change)
        slider.bind("<Motion>", self.update_slider_values)
        slider_value_label = ttk.Label(self.slider_frame, text=slider.get())
        slider_value_label.grid(row=grid_x, column=3*grid_y+2, padx=5, pady=5, stick="e")
        self.slidervalues[slider] = slider_value_label
        self.sliders[slidername] = slider

    def update_slider_values(self, event=None):
        for slider in self.slidervalues:
            self.slidervalues[slider].config(text=f"{slider.get():.3f}")

    def on_slider_change(self, event):
        self.run_hotline_guiparam()

    def mainloop(self):
        self.root.mainloop()

    def run_hotline_guiparam(self):
        self.n_charts = 0
        params = { k: v.get() for k, v in self.sliders.items() }
        run_hotline(**params)

    def hotline_show(self):
        fig = plt.gcf()
        fig.set_size_inches(6, 4)
        if self.n_charts <= len(self.canvases):
            canvas = FigureCanvasTkAgg(fig, master=self.chartframe)
            column = 2
            if "BLUE" in fig.axes[0].get_title().upper():
                column = 0
            if "RED" in fig.axes[0].get_title().upper():
                column = 1
            print()
            canvas.draw()
            canvas.get_tk_widget().grid(row=self.n_charts%2, column=column)
            self.canvases.append(canvas)
        else:
            self.canvases[self.n_charts].figure = fig
            self.canvases[self.n_charts].draw()
        self.n_charts += 1


if __name__ == "__main__":
    hgui = HotlineGUI()
    hgui.mainloop()