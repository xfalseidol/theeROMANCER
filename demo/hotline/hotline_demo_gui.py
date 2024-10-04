'''
RAND ROMANCER Hotline Demo, GUI

This is a limited front end to a single demo in ROMANCER,
demonstrating several integration techiques.
'''

import os.path
import threading

from casebasedreasoner.MOP_comparer_sorter import HLRComparerSorter
from casebasedreasoner.escalationladderreasoner import EscalationLadderCBR
from casebasedreasoner.util import export_cbr_sqlite, include_extra_csv_files_in_sqlite, make_networkx_graph, \
    make_graphviz_graph

from hotline_rules import ladder_csv_to_input_list
from hotline_demo import run_hotline
import tkinter as tk
from tkinter import ttk, filedialog
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from romancer.agent.amygdala import all_amygdala_archetypes


class HotlineGUI:
    _BLUE_AMYG_COMBOKEY = "blue"
    _RED_AMYG_COMBOKEY = "red"

    CHARTS_ACROSS = 2
    CHARTS_DOWN = 4

    TK_RED = "#ffbbbb"
    TK_BLUE = "light blue"
    TK_GREEN = "light green"

    # Generally when a frame of inputs is configured as a grid, use this padding
    INPUT_FRAME_PAD = 2

    def __init__(self):
        # for locking matplotlib
        self.matplotlib_lock = threading.RLock()

        # Non-GUI objects
        self.red_ladder_file = "data/ladder.csv"
        self.blue_ladder_file = "data/ladder.csv"

        self.blue_elcbr = EscalationLadderCBR(None, 0.0, name="BlueELCBR", comparer_sorter=HLRComparerSorter())
        self.red_elcbr = EscalationLadderCBR(None, 0.0, name="RedELCBR", comparer_sorter=HLRComparerSorter())

        # If we are stochastifying, hitting cancel sets this
        self.cancel_training = False

        # The charts come in via matplotlib.show(), we don't know what to expect. This tracks them.
        self.n_charts = 0
        self.canvases = []

        # GUI things
        self.root = tk.Tk()
        self.root.title("ROMANCER Hotline")
        self.root.wm_minsize(1024, 768)

        style = ttk.Style()
        style.configure("BlueNotebook.TNotebook", background=self.TK_BLUE)
        style.configure("RedNotebook.TNotebook", background=self.TK_RED)
        style.configure("BlueFrame.TFrame", background=self.TK_BLUE)
        style.configure("RedFrame.TFrame", background=self.TK_RED)
        style.configure("Blue.TLabel", background=self.TK_BLUE)
        style.configure("Red.TLabel", background=self.TK_RED)
        style.configure("Blue.Horizontal.TScale", background=self.TK_BLUE)
        style.configure("Red.Horizontal.TScale", background=self.TK_RED)
        style.configure("StochastifyFrame.TFrame", background=self.TK_GREEN)
        style.configure("Stochastify.TLabel", background=self.TK_GREEN)
        style.configure("Stochastify.TCheckbutton", background=self.TK_GREEN)

        self.controls_frame = ttk.Frame(self.root)
        self.controls_frame.pack()

        # Progress bar during training
        self.training_progress = None

        # Track all the GUI elements we need to draw from
        self.amygdala_choices = {a.short_desc() : a for a in all_amygdala_archetypes}
        self.amygdala_combos = {}
        self.ladder_entries = {}
        self.sliders = {}
        self.slidervalues = {}

        slider_frame = ttk.Frame(self.controls_frame)
        self.create_amygdala_inputs(slider_frame)
        # self.create_stochastify_inputs(slider_frame)

        # Status items for updating
        self.cbr_train_intval = tk.IntVar(value=0)
        self.cbr_run_intval = tk.IntVar(value=0)

        self.blue_cbr_status = tk.StringVar()
        self.red_cbr_status = tk.StringVar()
        self.train_status = tk.StringVar()

        # Main outputs go into tabs
        self.output_notebook = ttk.Notebook(self.root)

        # tkinter lets you overlay a canvas on another item

        self.chartframe = ttk.Frame(self.output_notebook)
        self.cbr_frame = ttk.Frame(self.output_notebook)
        self.about_rand_frame = ttk.Frame(self.output_notebook)

        self.output_notebook.add(self.chartframe, text="Run Charts")
        self.output_notebook.add(self.cbr_frame, text="CBR Training")
        self.output_notebook.add(self.about_rand_frame, text="About RAND")

        self.cbr_graph_frame = self.add_cbr_gui(self.cbr_frame)
        self.add_about_rand_frame(self.about_rand_frame)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)

        self.progress_variable = tk.StringVar(value="")
        progress_text = ttk.Label(self.root, textvariable=self.progress_variable)
        progress_text.pack(pady=self.INPUT_FRAME_PAD, padx=self.INPUT_FRAME_PAD)


        matplotlib_fontsize = 6
        plt.rcParams.update({
            "font.size": matplotlib_fontsize,
            "axes.titlesize": matplotlib_fontsize,
            "axes.labelsize": matplotlib_fontsize,
            "xtick.labelsize": matplotlib_fontsize,
            "ytick.labelsize": matplotlib_fontsize,
            "legend.fontsize": matplotlib_fontsize,
            "figure.titlesize": matplotlib_fontsize+2,
        })

        def show_capture():
            self.hotline_show()
        plt.show = show_capture

        # self.root.grid_rowconfigure(0, weight=1)
        # self.root.grid_columnconfigure(0, weight=1)
        # self.chartframe.grid_rowconfigure(0, weight=1)
        # self.chartframe.grid_columnconfigure(0, weight=1)

        def update_canvas_sizes(evt):
            new_width_px = self.chartframe.winfo_width() / self.CHARTS_ACROSS
            new_height_px = self.chartframe.winfo_height() / self.CHARTS_DOWN
            for canvas in self.canvases:
                canvas.get_tk_widget().config(width=new_width_px, height=new_height_px)
            self.cbr_graph_frame.config(width=self.chartframe.winfo_width(), height=self.chartframe.winfo_height())

        self.chartframe.bind('<Configure>', update_canvas_sizes)
        self.root.after(200, self.run_hotline_guiparam)

    def add_about_rand_frame(self, frame):
        logofile = "./randlogo.png"
        if os.path.exists(logofile):
            img = tk.PhotoImage(file=logofile)
            label = ttk.Label(frame, image=img)
            label.image = img # Keep a refernce to avoid GC
            label.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

        about_rand = '''
About RAND
        
RAND is a research organization that develops solutions to public policy challenges to help make communities throughout the world safer and more secure, healthier and more prosperous.
        
RAND is nonprofit, nonpartisan, and committed to the public interest.
        
To learn more about RAND, visit http://www.rand.org
        '''
        text_frame = ttk.Frame(frame)
        text_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True, padx=60, pady=60)
        text_widget.insert(tk.END, about_rand)
        text_widget.configure(state=tk.DISABLED)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

    def create_stochastify_inputs(self, slider_frame):
        frame = ttk.Frame(slider_frame, style = "StochastifyFrame.TFrame")
        slider_frame.grid_columnconfigure(2, weight=1)
        frame.grid(row=0, column=5, padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD, sticky="nsew")

        update_every_s = tk.IntVar(value=1)
        stochastify_checked = tk.IntVar(value=0)
        update_lbl = ttk.Label(frame, text="Re-run every (s):", style="Stochastify.TLabel")
        update_lbl.pack()
        update_spinner = ttk.Spinbox(frame, from_=1, to=30, textvariable=update_every_s)
        update_spinner.pack(padx=30)

        # Use closure to avoid needing to store more stuff in class
        def run_stochastify():
            is_checked = stochastify_checked.get() > 0
            if not is_checked:
                return
            self.run_hotline_guiparam()
            next_time_ms = 1000 * update_every_s.get()
            # print(f"Stoochastifying every {next_time_ms}")
            a = frame.after(next_time_ms, run_stochastify)

        run_check = ttk.Checkbutton(frame, text="Stochastify", variable=stochastify_checked, command=run_stochastify, style="Stochastify.TCheckbutton")
        run_check.pack()

    def create_amygdala_inputs_side(self, slider_frame, prefix_upper, prefix_lower, ladder_file, amyg_combokey):
        slider_frame_left = ttk.Frame(slider_frame, style=f"{prefix_upper}Frame.TFrame")
        slider_frame_left.pack(side=tk.LEFT, padx=(20, self.INPUT_FRAME_PAD), pady=self.INPUT_FRAME_PAD)
        slider_frame_right = ttk.Frame(slider_frame, style=f"{prefix_upper}Frame.TFrame")
        slider_frame_right.pack(side=tk.LEFT, padx=(self.INPUT_FRAME_PAD, 20), pady=self.INPUT_FRAME_PAD)

        fff_title = ttk.Label(slider_frame_right, text=f"{prefix_upper} F/F/F", style=f"{prefix_upper}.TLabel")
        fff_title.pack(padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD)
        fff_node = ttk.Label(slider_frame_right, text="(Default Amygdala Only)", style=f"{prefix_upper}.TLabel")
        fff_node.pack(padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD)

        fff_notebook = ttk.Notebook(slider_frame_right)

        fff_initial_frame = ttk.Frame(fff_notebook, style=f"{prefix_upper}Frame.TFrame")
        fff_weights_frame = ttk.Frame(fff_notebook, style=f"{prefix_upper}Frame.TFrame")

        fff_notebook.add(fff_initial_frame, text="Initial F/F/F")
        fff_notebook.add(fff_weights_frame, text="F/F/F Weights")

        fff_notebook.pack(fill=tk.BOTH, expand=True)

        amyg_title = ttk.Label(slider_frame_left, text=f"{prefix_upper} Temperament", style=f"{prefix_upper}.TLabel")
        amyg_row = 0
        amyg_title.grid(row=amyg_row, column=0, columnspan=3)
        amyg_row += 1

        self.create_ladder_chooser(slider_frame_left, ladder_file, amyg_combokey, amyg_row)
        amyg_row += 1
        self.create_amygdala_choice(slider_frame_left, "Amygdala", amyg_combokey, amyg_row, f"{prefix_upper}.TLabel")
        amyg_row += 1
        self.create_slider(slider_frame_left, "Response Threshold", f"{prefix_lower}_response_threshhold", 0.0, 1.0, 0.2, amyg_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")
        amyg_row += 1
        self.create_slider(slider_frame_left, "Initial PBF", f"{prefix_lower}_initial_pbf", 0.0, 1.0, 0.001, amyg_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")
        amyg_row += 1
        self.create_slider(slider_frame_left, "PBF Halflife", f"{prefix_lower}_pbf_halflife", 0.0, 100000.0, 38400, amyg_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")
        amyg_row += 1

        fff_row = 0
        self.create_slider(fff_initial_frame, "Initial Fight", f"{prefix_lower}_initial_fight", 0.0, 1.0, 0.0, fff_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")
        fff_row += 1
        self.create_slider(fff_initial_frame, "Initial Freeze", f"{prefix_lower}_initial_freeze", 0.0, 1.0, 0.0, fff_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")
        fff_row += 1
        self.create_slider(fff_initial_frame, "Initial Flight", f"{prefix_lower}_initial_flight", 0.0, 1.0, 0.0, fff_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")

        fff_weight_row = 0
        self.create_slider(fff_weights_frame, "Fight Weight", f"{prefix_lower}_weight_fight", 0.0, 1.0, 1.0, fff_weight_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")
        fff_weight_row += 1
        self.create_slider(fff_weights_frame, "Freeze Weight", f"{prefix_lower}_weight_freeze", 0.0, 1.0, 1.0, fff_weight_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")
        fff_weight_row += 1
        self.create_slider(fff_weights_frame, "Flight Weight", f"{prefix_lower}_weight_flight", 0.0, 1.0, 1.0, fff_weight_row, f"{prefix_upper}.TLabel", f"{prefix_upper}.Horizontal.TScale")

    def create_amygdala_inputs(self, slider_frame):
        slider_frame.grid(padx=1, pady=1, row=0, column=0)

        self.create_amygdala_inputs_side(slider_frame, "Blue", "blue", self.blue_ladder_file, self._BLUE_AMYG_COMBOKEY)
        self.create_amygdala_inputs_side(slider_frame, "Red", "red", self.red_ladder_file, self._RED_AMYG_COMBOKEY)



    def save_cbr_func(self):
        blue_sqlite = "blue_hotline_elcbr.sqlite"
        red_sqlite = "red_hotline_elcbr.sqlite"

        blue_csvs = ladder_csv_to_input_list(self.ladder_entries[self._BLUE_AMYG_COMBOKEY].get())
        include_extra_csv_files_in_sqlite(blue_sqlite, blue_csvs)
        export_cbr_sqlite(self.blue_elcbr, blue_sqlite)
        red_csvs = ladder_csv_to_input_list(self.ladder_entries[self._RED_AMYG_COMBOKEY].get())
        include_extra_csv_files_in_sqlite(red_sqlite, red_csvs)
        export_cbr_sqlite(self.red_elcbr, red_sqlite)

        make_graphviz_graph(self.blue_elcbr, "blue_elcbr.dot")
        make_graphviz_graph(self.red_elcbr, "red_elcbr.dot")


    def add_cbr_gui(self, parent_frame):

        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=0)
        parent_frame.grid_columnconfigure(1, weight=1)

        cbr_train_frame = ttk.Frame(parent_frame, width=400)
        cbr_train_frame.grid(row=0, column=0, sticky="ns")

        cbr_graph_frame = ttk.Frame(parent_frame)
        cbr_graph_frame.grid(row=0, column=1, sticky="nsew")


        # self.root.grid_rowconfigure(0, weight=1)
        # self.root.grid_columnconfigure(0, weight=1)
        # self.chartframe.grid_rowconfigure(0, weight=1)
        # self.chartframe.grid_columnconfigure(0, weight=1)

        train_check = ttk.Checkbutton(cbr_train_frame, text="Train CBRs", variable=self.cbr_train_intval)
        train_check.pack(fill=tk.X, padx=5, pady=5)
        run_check = ttk.Checkbutton(cbr_train_frame, text="Run CBRs", variable=self.cbr_run_intval)
        run_check.pack(fill=tk.X, padx=5, pady=5)

        run_many_button = ttk.Button(cbr_train_frame, text="Train", command=self.train_click)
        run_many_button.pack(fill=tk.X, padx=5, pady=5)

        cancel_training_button = ttk.Button(cbr_train_frame, text="Cancel Training", command=self.canceltraining_click)
        cancel_training_button.pack(fill=tk.X, padx=5, pady=5)

        cbr_training_frame = ttk.Frame(cbr_train_frame)
        cbr_training_frame.pack()

        train_label = ttk.Label(cbr_training_frame, text="Training Progress")
        train_label.pack()
        self.training_progress = ttk.Progressbar(cbr_training_frame)
        self.training_progress.pack(fill=tk.X, expand=True, padx=5, pady=5)

        cbr_stochastify_status = ttk.Label(cbr_train_frame, textvariable=self.train_status)
        cbr_stochastify_status.pack()

        bluelabel = ttk.Label(cbr_train_frame, textvariable=self.blue_cbr_status)
        bluelabel.pack(padx=5, pady=5)
        redlabel = ttk.Label(cbr_train_frame, textvariable=self.red_cbr_status)
        redlabel.pack(padx=5, pady=5)
        savebutton = ttk.Button(cbr_train_frame, text="Export CBRs", command=self.save_cbr_func)
        savebutton.pack(fill=tk.X)
        return cbr_graph_frame


    def create_ladder_chooser(self, parent_frame, default_file, name, grid_row):
        entry = ttk.Entry(parent_frame)
        entry.insert(0, default_file)
        entry.grid(row=grid_row, column=1, sticky="ew", padx=self.INPUT_FRAME_PAD)
        self.ladder_entries[name] = entry

        def select_file():
            file_path = filedialog.askopenfilename(title="Choose Ladder CSV File",
                                                   initialdir=os.path.dirname(default_file),
                                                   filetypes=[("CSV Files", "*.csv")])
            if file_path:
                rel_path = os.path.relpath(file_path)
                entry.delete(0, tk.END)
                entry.insert(0, rel_path)
                # The CBR is tied to the ladder, create a new one
                if name == "blue":
                    self.blue_elcbr = EscalationLadderCBR(None, 0.0, name="BlueELCBR", comparer_sorter=HLRComparerSorter())
                elif name == "red":
                    self.red_elcbr = EscalationLadderCBR(None, 0.0, name="RedELCBR", comparer_sorter=HLRComparerSorter())
                else:
                    print(f"Don't know how to recreate a elcbr for {name}")
                self.run_hotline_guiparam()

        button = ttk.Button(parent_frame, text=f"Choose {name} Ladder", command=select_file)
        button.grid(row=grid_row, column=0, padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD, sticky="e")


    def create_amygdala_choice(self, parent_frame, label, name, grid_row, labelstyle):
        dropdown_options = [k for k in self.amygdala_choices.keys()]
        dropdown_var = tk.StringVar(value=dropdown_options[0])
        self.amygdala_combos[name] = dropdown_var
        combo_label = ttk.Label(parent_frame, text=label, style=labelstyle)
        combo_label.grid(row=grid_row, column=0, padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD, sticky="e")
        dropdown = ttk.Combobox(parent_frame, textvariable=dropdown_var)
        dropdown['values'] = dropdown_options
        dropdown.set(dropdown_options[0])
        dropdown.bind("<<ComboboxSelected>>", self.on_slider_change)
        dropdown.grid(row=grid_row, column=1, padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD, sticky="ew")

    def canceltraining_click(self):
        self.cancel_training = True

    def train_click(self):
        self.cancel_training = False
        thread = threading.Thread(target=self.do_training)
        thread.start()

    def do_training(self, n_train_times=10, n_run_times=20, orig_n_train_times=None, orig_n_run_times=None):
        if self.cancel_training:
            self.train_status.set(f"Training cancelled")
            return

        if orig_n_train_times is None:
            self.training_progress.configure(maximum=n_train_times + n_run_times, variable=tk.IntVar(value=0))
            orig_n_train_times = n_train_times
        if orig_n_run_times is None:
            orig_n_run_times = n_run_times

        next_n_run_times = n_run_times
        next_n_train_times = n_train_times

        if 0 < n_train_times:
            self.train_status.set(f"Train: {orig_n_train_times - n_train_times + 1}/{orig_n_train_times}")
            self.cbr_run_intval.set(0)
            self.cbr_train_intval.set(1)
            next_n_train_times -= 1
        elif 0 < n_run_times:
            self.train_status.set(f"Run: {orig_n_run_times - n_run_times + 1}/{orig_n_run_times}")
            self.cbr_run_intval.set(1)
            self.cbr_train_intval.set(0)
            next_n_run_times -= 1
        else:
            self.train_status.set("Training Complete")
            return

        self.run_hotline_guiparam(run_threaded=False)

        self.training_progress.step()

        self.root.after(200, self.do_training, next_n_train_times, next_n_run_times, orig_n_train_times, orig_n_run_times)

    def create_slider(self, parent_frame, sliderlabel, slidername, slidermin, slidermax, sliderdefault, grid_x, labelstyle, sliderstyle):
        slider_label = ttk.Label(parent_frame, text=sliderlabel, style=labelstyle)
        slider_label.grid(row=grid_x, column=0, padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD, sticky="e")
        slider = ttk.Scale(parent_frame, from_=slidermin, to=slidermax, orient="horizontal", style=sliderstyle)
        slider.set(sliderdefault)
        slider.grid(row=grid_x, column=1, padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD, sticky="ew")
        slider.bind("<ButtonRelease-1>", self.on_slider_change)
        slider.bind("<Motion>", self.update_slider_values)
        slider_value_label = ttk.Label(parent_frame, text=slider.get(), style=labelstyle)
        slider_value_label.grid(row=grid_x, column=2, padx=self.INPUT_FRAME_PAD, pady=self.INPUT_FRAME_PAD, stick="w")
        self.slidervalues[slider] = slider_value_label
        self.sliders[slidername] = slider

    def update_cbr_training_frame(self):
        self.red_cbr_status.set(f"Red ELCBR Mops: {len(self.red_elcbr.mops)}")
        self.blue_cbr_status.set(f"Blue ELCBR Mops: {len(self.blue_elcbr.mops)}")


    def update_slider_values(self, event=None):
        for slider in self.slidervalues:
            self.slidervalues[slider].config(text=f"{slider.get():.2f}")

    def enable_disable_sliders(self):
        blue_default_sliders = [f"blue_{cat}_{fff}" for fff in ["fight", "freeze", "flight"] for cat in ["weight", "initial"]]
        curr_blue_amyg = self.amygdala_combos[self._BLUE_AMYG_COMBOKEY].get()
        blue_new_state = tk.NORMAL if "Default" in curr_blue_amyg else tk.DISABLED
        for slidername in blue_default_sliders:
            self.sliders[slidername].config(state=blue_new_state)

        red_default_sliders = [f"red_{cat}_{fff}" for fff in ["fight", "freeze", "flight"] for cat in ["weight", "initial"]]
        curr_red_amyg = self.amygdala_combos[self._RED_AMYG_COMBOKEY].get()
        red_new_state = tk.NORMAL if "Default" in curr_red_amyg else tk.DISABLED
        for slidername in red_default_sliders:
            self.sliders[slidername].config(state=red_new_state)


    def on_slider_change(self, event):
        self.enable_disable_sliders()
        self.run_hotline_guiparam()

    def mainloop(self):
        self.root.mainloop()

    def render_graph(self, cbrinst):
        g = make_networkx_graph(cbrinst, ["M-PATTERN", "M_percept", "M_percept_group", "M_ELRScenario_outcome"], ["M_ELRScenario", "M-ROOT"],
                                include_inheritance_edges=False)
        fig, ax = plt.subplots(figsize=(10, 10))

        width_px = float(self.cbr_graph_frame.winfo_width())
        height_px = float(self.cbr_graph_frame.winfo_height())
        width_in = width_px / fig.dpi
        height_in = height_px / fig.dpi
        fig.set_size_inches(width_in, height_in)
        pos = nx.spring_layout(g)
        nx.draw(g, pos, ax=ax, with_labels=True, node_color="lightblue", edge_color="gray", node_size=10, font_size=10)
        for widget in self.cbr_graph_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.cbr_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plt.close()

    def run_hotline_guiparam(self, run_threaded=True):
        def do():
            self.n_charts = 0
            cbr_train = True if self.cbr_train_intval and self.cbr_train_intval.get()>0 else False
            cbr_run = True if self.cbr_run_intval and self.cbr_run_intval.get()>0 else False
            params = { k: v.get() for k, v in self.sliders.items() }
            params["red_amyg"] = self.amygdala_choices[self.amygdala_combos[self._RED_AMYG_COMBOKEY].get()]
            params["blue_amyg"] = self.amygdala_choices[self.amygdala_combos[self._BLUE_AMYG_COMBOKEY].get()]
            params["blue_elcbr"] = self.blue_elcbr if cbr_train or cbr_run else None
            params["red_elcbr"] = self.red_elcbr if cbr_train or cbr_run else None
            params["red_train_elcbr"] = params["blue_train_elcbr"] = cbr_train
            params["red_run_elcbr"] = params["blue_run_elcbr"] = cbr_run
            params["blue_ladder_file"] = self.ladder_entries[self._BLUE_AMYG_COMBOKEY].get()
            params["red_ladder_file"] = self.ladder_entries[self._RED_AMYG_COMBOKEY].get()

            def time_cb(time):
                '''
                This gets called as the simulation progresses
                '''
                if time is None:
                    self.progress_variable.set(f"Complete")
                else:
                    self.progress_variable.set(f"T={time}")

            run_hotline(**params, time_cb=time_cb, matplotlib_lock=self.matplotlib_lock)
            # self.render_graph(self.blue_elcbr)
            self.update_cbr_training_frame()

        if run_threaded:
            thread = threading.Thread(target=do)
            thread.start()
        else:
            do()

    def hotline_show(self):
        self.matplotlib_lock.acquire()
        fig = plt.gcf()
        # Four charts high, two wide
        width_px = float(self.chartframe.winfo_width()) / self.CHARTS_ACROSS
        height_px = float(self.chartframe.winfo_height()) / self.CHARTS_DOWN
        width_in = max(3.0, (width_px / fig.dpi))
        height_in = max(1.5, (height_px / fig.dpi))
        fig.set_size_inches(width_in, height_in)
        if self.n_charts <= len(self.canvases):
            canvas = FigureCanvasTkAgg(fig, master=self.chartframe)
            titles = [ax.get_title().upper() for ax in fig.axes]
            column = 2
            if any(["BLUE" in t for t in titles]):
                column = 0
            elif any(["RED" in t for t in titles]):
                column = 1

            row = 5
            if any(["LADDER" in t for t in titles]):
                row = 1
            elif any(["RESOLVE" in t for t in titles]):
                row = 2
            elif any(["MOOD" in t for t in titles]):
                row = 3
            elif any(["TIMELINE" in t for t in titles]):
                row = 4

            print()
            canvas.draw()
            canvas.get_tk_widget().grid(row=row, column=column)
            canvas.get_tk_widget().config(width=width_px, height=height_px)
            self.canvases.append(canvas)
        else:
            self.canvases[self.n_charts].figure = fig
            self.canvases[self.n_charts].get_tk_widget().config(width=width_px, height=height_px)
            self.canvases[self.n_charts].draw()
        self.n_charts += 1
        self.matplotlib_lock.release()


if __name__ == "__main__":
    hgui = HotlineGUI()
    hgui.mainloop()
