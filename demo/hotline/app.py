from tempfile import tempdir
import asyncio
from shiny import App, reactive, render, ui
from shiny.types import ImgData

from hotline_demo import run_hotline
import matplotlib.pyplot as plt
import os
import base64
import tempfile

img_width_shiny = 4
app_ui = ui.page_fillable(
    ui.tags.style(
        '''
        body {
            font-size: 12px;
        }
        .card-body img {
            margin-bottom: 5px;
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
                ui.input_slider("blue_pbf_halflife", "PBF Halflife (days):", min=0, max=5, value=1)
            ),
            ui.card(
                ui.p("Red Temperament"),
                {"class": "card card-red"},
                ui.input_slider("red_response_threshold", "Response Threshold:", min=0, max=100, value=70),
                ui.input_slider("red_initial_pbf", "Initial PBF:", min=0, max=100, value=2),
                ui.input_slider("red_pbf_halflife", "PBF Halflife (days):", min=0, max=3, value=1)
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

chartdir = "./chartdir"
if not os.path.exists(chartdir):
    os.mkdir(chartdir)

def server(input, output, session):
    def run_shiny_hotline():
        blue_initial_pbf = session.input["blue_initial_pbf"]() / 100.0
        blue_pbf_halflife = session.input["blue_pbf_halflife"]() * 38400
        blue_response_threshold = session.input["blue_response_threshold"]() / 100.0

        red_initial_pbf = session.input["red_initial_pbf"]() / 100.0
        red_pbf_halflife = session.input["red_pbf_halflife"]() * 38400
        red_response_threshold = session.input["red_response_threshold"]() / 100.0
        run_hotline(blue_initial_pbf=blue_initial_pbf, blue_pbf_halflife=blue_pbf_halflife, blue_response_threshhold=blue_response_threshold,
                    red_initial_pbf=red_initial_pbf, red_pbf_halflife=red_pbf_halflife, red_response_threshhold=red_response_threshold)

    @reactive.effect
    def _():
        run_shiny_hotline()

    matplotlib_fontsize = 6.5
    plt.rcParams.update({
        "font.size": matplotlib_fontsize,
        "axes.titlesize": matplotlib_fontsize,
        "axes.labelsize": matplotlib_fontsize,
        "xtick.labelsize": matplotlib_fontsize,
        "ytick.labelsize": matplotlib_fontsize,
        "legend.fontsize": matplotlib_fontsize,
        "figure.titlesize": matplotlib_fontsize + 2,
    })

    chart_imgs = {}

    hack_trigger = reactive.Value(0)

    @output
    @render.image
    def blue_timeline():
        hack_trigger()
        chart_img = chart_imgs["BLUE TIMELINE"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_timeline():
        chart_img = chart_imgs["RED TIMELINE"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def blue_amygdala():
        hack_trigger()
        chart_img = chart_imgs["BLUE MOOD METER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_amygdala():
        chart_img = chart_imgs["RED MOOD METER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def blue_ladder():
        chart_img = chart_imgs["BLUE ESCALATION LADDER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_ladder():
        chart_img = chart_imgs["RED ESCALATION LADDER"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def blue_resolve():
        chart_img = chart_imgs["BLUE RESOLVE"]
        retval: ImgData = {"src": f"{chartdir}/{chart_img}"}
        return retval

    @output
    @render.image
    def red_resolve():
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

        thisimg = tempfile.mktemp(".png", base64.b64encode(this_title.encode("ascii")).decode("utf-8"), chartdir)
        print("This img: " + thisimg)
        thisfname = os.path.basename(thisimg)
        # thisfname = base64.b64encode(this_title.encode("ascii")).decode("utf-8") + ".png"
        # thisimg = os.path.join(chartdir, thisfname)
        plt.savefig(thisimg, format='png')
        chart_imgs[this_title] = thisfname

    plt.show = matplotlib_capture

app = App(app_ui, server, static_assets={"/charts": os.path.join(os.path.dirname(__file__), chartdir)})

if __name__ == "__main__":
    app.run()
