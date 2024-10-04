from shiny import App, reactive, render, ui
from shiny.types import ImgData

from hotline_demo import run_hotline
from romancer.agent.amygdala import all_amygdala_archetypes
import matplotlib.pyplot as plt
import os
import tempfile

# Matplotlib needs inches. This is how many of those.
img_width_shiny = 4

amygdala_choices = {a.short_desc(): a for a in all_amygdala_archetypes}
ladders = {
    "Default": "data/ladder.csv",
    "4 Rung": "data/four_rungs.csv"
}

app_ui = ui.page_fillable(
    ui.tags.style(
        '''
        body {
            font-size: 12px;
        }
        .shiny-image-output {
            width: auto !important;
            height: auto !important;
        }
        .card-body img {
            # margin-bottom: 5px;
            width: auto !important;
            height: auto !important;
        }
        .card-blue {
            background-color: lightblue;
        }
        .card-red {
            background-color: lightcoral;
        }
        '''
    ),
    ui.page_sidebar(
        ui.sidebar(
            ui.card(
                {"class": "card card-blue"},
                ui.p("Blue Temperament"),
                ui.input_slider("blue_response_threshold", "Response Threshold:", min=0, max=100, value=20),
                ui.input_slider("blue_initial_pbf", "Initial PBF:", min=0, max=100, value=2),
                ui.input_slider("blue_pbf_halflife", "PBF Halflife (days):", min=0, max=5, value=1),
                ui.input_select("blue_amygdala", "Amygdala Archetype", choices=list(amygdala_choices.keys())),
                ui.input_select("blue_ladder", "Escalation Ladder", choices=list(ladders.keys()))
            ),
            ui.card(
                ui.p("Red Temperament"),
                {"class": "card card-red"},
                ui.input_slider("red_response_threshold", "Response Threshold:", min=0, max=100, value=70),
                ui.input_slider("red_initial_pbf", "Initial PBF:", min=0, max=100, value=2),
                ui.input_slider("red_pbf_halflife", "PBF Halflife (days):", min=0, max=3, value=1),
                ui.input_select("red_amygdala", "Amygdala Archetype", choices=list(amygdala_choices.keys())),
                ui.input_select("red_ladder", "Escalation Ladder", choices=list(ladders.keys()))
            )
        ),
        ui.layout_column_wrap(
            ui.card(
                {"class": "card card-blue"},
                ui.output_image("blue_ladder"),
                ui.output_image("blue_resolve"),
                ui.output_image("blue_amygdala"),
                ui.output_image("blue_timeline")
            ),
            ui.card(
            {"class": "card card-red"},
                ui.output_image("red_ladder"),
                ui.output_image("red_resolve"),
                ui.output_image("red_amygdala"),
                ui.output_image("red_timeline")
            )

        ),
        title = "ROMANCER Hotline",
        window_title = "RAND Hotline",
)

)

def on_slider_change(value):
    print(f"Slider value changed to {value}")

chartdir = "chartdir"
if not os.path.exists(chartdir):
    os.mkdir(chartdir)

def server(input, output, session):
    def run_shiny_hotline():
        blue_initial_pbf = session.input["blue_initial_pbf"]() / 100.0
        blue_pbf_halflife = session.input["blue_pbf_halflife"]() * 38400
        blue_response_threshold = session.input["blue_response_threshold"]() / 100.0
        blue_amygdala_name = session.input["blue_amygdala"]()
        blue_amygdala = amygdala_choices[blue_amygdala_name]
        blue_ladder = ladders[session.input["blue_ladder"]()]

        red_initial_pbf = session.input["red_initial_pbf"]() / 100.0
        red_pbf_halflife = session.input["red_pbf_halflife"]() * 38400
        red_response_threshold = session.input["red_response_threshold"]() / 100.0
        red_amygdala_name = session.input["red_amygdala"]()
        red_amygdala = amygdala_choices[red_amygdala_name]
        red_ladder = ladders[session.input["red_ladder"]()]

        run_hotline(blue_initial_pbf=blue_initial_pbf, blue_pbf_halflife=blue_pbf_halflife, blue_response_threshhold=blue_response_threshold,
                    blue_amyg=blue_amygdala, blue_ladder_file=blue_ladder,
                    red_initial_pbf=red_initial_pbf, red_pbf_halflife=red_pbf_halflife, red_response_threshhold=red_response_threshold,
                    red_amyg=red_amygdala, red_ladder_file=red_ladder
                    )

    @reactive.effect
    def _():
        run_shiny_hotline()

    matplotlib_fontsize = 6.5
    plt.rcParams.update({
        "font.size": matplotlib_fontsize,
        "axes.titlesize": matplotlib_fontsize + 2,
        "axes.labelsize": matplotlib_fontsize,
        "xtick.labelsize": matplotlib_fontsize,
        "ytick.labelsize": matplotlib_fontsize,
        "legend.fontsize": matplotlib_fontsize,
        "figure.titlesize": matplotlib_fontsize + 2,
    })

    chart_imgs = {}

    # Shiny wants the output images to reference the inputs they rely on.
    def reference_all_inputs():
        # Cannot find documentation on a way to do this programmatically,
        #   or without accessing members with underscore prefixes
        inputs = []
        for side in ["blue", "red"]:
            inputs.extend([f"{side}_initial_pbf", f"{side}_pbf_halflife", f"{side}_response_threshold",
                           f"{side}_amygdala", f"{side}_ladder"])
        _ = [session.input[q]() for q in inputs]

    @output
    @render.image
    def blue_timeline():
        reference_all_inputs()
        chart_img = chart_imgs["BLUE TIMELINE"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_timeline():
        reference_all_inputs()
        chart_img = chart_imgs["RED TIMELINE"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def blue_amygdala():
        reference_all_inputs()
        chart_img = chart_imgs["BLUE MOOD METER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_amygdala():
        reference_all_inputs()
        chart_img = chart_imgs["RED MOOD METER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def blue_ladder():
        reference_all_inputs()
        chart_img = chart_imgs["BLUE ESCALATION LADDER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_ladder():
        reference_all_inputs()
        chart_img = chart_imgs["RED ESCALATION LADDER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def blue_resolve():
        reference_all_inputs()
        chart_img = chart_imgs["BLUE RESOLVE"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_resolve():
        reference_all_inputs()
        chart_img = chart_imgs["RED RESOLVE"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    # All the chart rendering just happens inside the model. We capture it here
    def matplotlib_capture():
        fig = plt.gcf()
        fig.set_size_inches(5, 3)
        titles = [ax.get_title().upper() for ax in fig.axes]
        this_title = titles[0]
        for t in titles:
            if len(t) > 0:
                this_title = t

        thisimg = tempfile.mktemp(".png", dir=chartdir)
        thisfname = os.path.basename(thisimg)
        plt.savefig(thisimg, format='png')
        chart_imgs[this_title] = thisfname

    plt.show = matplotlib_capture

app = App(app_ui, server, static_assets={f"/{chartdir}": os.path.join(os.path.dirname(__file__), chartdir)})

if __name__ == "__main__":
    app.run()
