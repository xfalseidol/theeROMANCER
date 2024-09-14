from hotline_demo import run_hotline
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from romancer.agent.amygdala import all_amygdala_archetypes


class HotlineGUI:
    def __init__(self):
        self.n_charts = 0
        self.canvases = []
        self.root = tk.Tk()
        self.root.title("ROMANCER Hotline")

        self.amygdala_choices = {a.short_desc() : a for a in all_amygdala_archetypes}
        self.amygdala_combos = {}
        self._BLUE_AMYG_COMBOKEY = "blue"
        self._RED_AMYG_COMBOKEY = "red"

        self.sliders = {}
        self.slidervalues = {}
        self.slider_frame = tk.Frame(self.root)
        self.slider_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=10)

        self.create_slider("Blue Response Threshold", "blue_response_threshhold", 0.0, 1.0, 0.2, 0, 0)
        self.create_slider("Blue Initial PBF", "blue_initial_pbf", 0.0, 1.0, 0.001, 1, 0)
        self.create_slider("Blue PBF Halflife", "blue_pbf_halflife", 0.0, 100000.0, 38400, 2, 0)

        self.create_slider("Red Response Threshold", "red_response_threshhold", 0.0, 1.0, 0.7, 0, 1)
        self.create_slider("Red Initial PBF", "red_initial_pbf", 0.0, 1.0, 0.001, 1, 1)
        self.create_slider("Red PBF Halflife", "red_pbf_halflife", 0.0, 100000.0, 38400, 2, 1)

        self.create_amygdala_choice("Blue Amygdala", self._BLUE_AMYG_COMBOKEY, 3, 0)
        self.create_amygdala_choice("Red Amygdala", self._RED_AMYG_COMBOKEY, 3, 1)
        print(self.amygdala_choices)

        #
        # self.run_button = ttk.Button(self.root, text="Run", command=self.run_hotline_guiparam)
        # self.run_button.pack()

        self.chartframe = ttk.Frame(self.root)
        self.chartframe.pack()

        def show_capture():
            self.hotline_show()
        plt.show = show_capture
        self.run_hotline_guiparam()

    def create_amygdala_choice(self, label, name, grid_row, grid_col):
        dropdown_options = [k for k in self.amygdala_choices.keys()]
        dropdown_var = tk.StringVar(value=dropdown_options[0])
        self.amygdala_combos[name] = dropdown_var
        combo_label = ttk.Label(self.slider_frame, text=label)
        combo_label.grid(row=grid_row, column=3 * grid_col, padx=5, pady=5, sticky="w")
        dropdown = ttk.Combobox(self.slider_frame, textvariable=dropdown_var)
        dropdown['values'] = dropdown_options
        dropdown.set(dropdown_options[0])
        dropdown.bind("<<ComboboxSelected>>", self.on_slider_change)
        dropdown.grid(row=grid_row, column=3 * grid_col + 1, padx=5, pady=5)

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
        params["red_amyg"] = self.amygdala_choices[self.amygdala_combos[self._RED_AMYG_COMBOKEY].get()]
        params["blue_amyg"] = self.amygdala_choices[self.amygdala_combos[self._BLUE_AMYG_COMBOKEY].get()]
        run_hotline(**params)

    def hotline_show(self):
        fig = plt.gcf()
        fig.set_size_inches(5, 2)
        if self.n_charts <= len(self.canvases):
            canvas = FigureCanvasTkAgg(fig, master=self.chartframe)
            titles = [ax.get_title().upper() for ax in fig.axes]
            column = 2
            if any(["BLUE" in t for t in titles]):
                column = 0
            elif any(["RED" in t for t in titles]):
                column = 1

            row = 5
            if any(["RESOLVE" in t for t in titles]):
                row = 1
            elif any(["LADDER" in t for t in titles]):
                row = 2
            elif any(["MOOD" in t for t in titles]):
                row = 3
            elif any(["TIMELINE" in t for t in titles]):
                row = 4

            print()
            canvas.draw()
            canvas.get_tk_widget().grid(row=row, column=column)
            self.canvases.append(canvas)
        else:
            self.canvases[self.n_charts].figure = fig
            self.canvases[self.n_charts].draw()
        self.n_charts += 1


if __name__ == "__main__":
    hgui = HotlineGUI()
    hgui.mainloop()