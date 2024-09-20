from casebasedreasoner.escalationladderreasoner import EscalationLadderCBR
from casebasedreasoner.util import export_cbr_sqlite, include_extra_csv_files_in_sqlite
from demo.hotline.hotline_rules import ladder_csv_to_input_list
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

        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack()

        self.amygdala_choices = {a.short_desc() : a for a in all_amygdala_archetypes}
        self.amygdala_combos = {}
        self._BLUE_AMYG_COMBOKEY = "blue"
        self._RED_AMYG_COMBOKEY = "red"

        self.ladder_file = "data/ladder.csv"

        self.sliders = {}
        self.slidervalues = {}
        self.slider_frame = tk.Frame(self.controls_frame)
        self.slider_frame.grid(padx=10, pady=10, row=0, column=0)

        self.create_slider("Blue Response Threshold", "blue_response_threshhold", 0.0, 1.0, 0.2, 0, 0)
        self.create_slider("Blue Initial PBF", "blue_initial_pbf", 0.0, 1.0, 0.001, 1, 0)
        self.create_slider("Blue PBF Halflife", "blue_pbf_halflife", 0.0, 100000.0, 38400, 2, 0)

        self.create_slider("Red Response Threshold", "red_response_threshhold", 0.0, 1.0, 0.7, 0, 1)
        self.create_slider("Red Initial PBF", "red_initial_pbf", 0.0, 1.0, 0.001, 1, 1)
        self.create_slider("Red PBF Halflife", "red_pbf_halflife", 0.0, 100000.0, 38400, 2, 1)

        self.create_amygdala_choice("Blue Amygdala", self._BLUE_AMYG_COMBOKEY, 3, 0)
        self.create_amygdala_choice("Red Amygdala", self._RED_AMYG_COMBOKEY, 3, 1)

        self.blue_elcbr = EscalationLadderCBR(None, 0.0, name="BlueELCBR")
        self.red_elcbr = EscalationLadderCBR(None, 0.0, name="RedELCBR")

        self.cbr_train_intval = tk.IntVar(value=1)
        self.cbr_run_intval = tk.IntVar(value=0)

        self.cbr_frame = tk.Frame(self.controls_frame)
        self.cbr_frame.grid(row=0, column=1)

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

    def update_cbr_training_frame(self):
        for widget in self.cbr_frame.winfo_children():
            widget.destroy()
        bluelabel = ttk.Label(self.cbr_frame, text=f"Blue ELCBR Mops: {len(self.blue_elcbr.mops)}")
        bluelabel.grid(row=0, column=0, padx=5, pady=5)
        redlabel = ttk.Label(self.cbr_frame, text=f"Red ELCBR Mops: {len(self.red_elcbr.mops)}")
        redlabel.grid(row=1, column=0, padx=5, pady=5)
        train_check = ttk.Checkbutton(self.cbr_frame, text="Train CBRs", variable=self.cbr_train_intval)
        train_check.grid(row=2, column=0, padx=5, pady=5)
        run_check = ttk.Checkbutton(self.cbr_frame, text="Run CBRs", variable=self.cbr_run_intval)
        run_check.grid(row=3, column=0, padx=5, pady=5)

        def save_func():
            blue_sqlite = "blue_hotline_elcbr.sqlite"
            red_sqlite = "red_hotline_elcbr.sqlite"

            export_cbr_sqlite(self.blue_elcbr, blue_sqlite)
            blue_csvs = ladder_csv_to_input_list(self.ladder_file)
            include_extra_csv_files_in_sqlite(blue_sqlite, blue_csvs)
            export_cbr_sqlite(self.red_elcbr, red_sqlite)
            red_csvs = ladder_csv_to_input_list(self.ladder_file)
            include_extra_csv_files_in_sqlite(red_sqlite, red_csvs)

        savebutton = ttk.Button(self.cbr_frame, text="Export CBRs", command=save_func)
        savebutton.grid(row=4, column=0, padx=5, pady=5)


    def update_slider_values(self, event=None):
        for slider in self.slidervalues:
            self.slidervalues[slider].config(text=f"{slider.get():.3f}")

    def on_slider_change(self, event):
        self.run_hotline_guiparam()

    def mainloop(self):
        self.root.mainloop()

    def run_hotline_guiparam(self):
        self.n_charts = 0
        cbr_train = True if self.cbr_train_intval and self.cbr_train_intval.get()>0 else False
        cbr_run = True if self.cbr_run_intval and self.cbr_run_intval.get()>0 else False
        params = { k: v.get() for k, v in self.sliders.items() }
        params["red_amyg"] = self.amygdala_choices[self.amygdala_combos[self._RED_AMYG_COMBOKEY].get()]
        params["blue_amyg"] = self.amygdala_choices[self.amygdala_combos[self._BLUE_AMYG_COMBOKEY].get()]
        params["blue_elcbr"] = self.blue_elcbr
        params["red_elcbr"] = self.red_elcbr
        params["red_train_elcbr"] = params["blue_train_elcbr"] = cbr_train
        params["red_run_elcbr"] = params["blue_run_elcbr"] = cbr_run
        params["blue_ladder_file"] = params["red_ladder_file"] = self.ladder_file

        run_hotline(**params)
        self.update_cbr_training_frame()

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