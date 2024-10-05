from shiny import App, reactive, render, ui
from shiny.types import ImgData

from hotline_demo import run_hotline
from romancer.agent.amygdala import all_amygdala_archetypes
import base64 as b64
import matplotlib.pyplot as plt
import os
import tempfile

# Require a trivially simple challenge/response to enter the page.
#  This does not provide any real protection, the password is stored in javascript
challenge = "How I Learned to Stop Worrying"
response = "Strangelove"

amygdala_choices = {a.short_desc(): a for a in all_amygdala_archetypes}
ladders = {
    "Default": "data/ladder.csv",
    "4 Rung": "data/four_rungs.csv"
}

rand_svg_binary = open("./randlogo.svg", "rb").read()
rand_svg_base64_str = b64.b64encode(rand_svg_binary).decode("utf-8")
rand_svg_uri = f"data:image/svg+xml;base64,{rand_svg_base64_str}"

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
            display: block;
            # margin-bottom: 5px;
            width: auto !important;
            height: auto !important;
        }
        .column-wrap {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-start;
            align-items: flex-start;
            width: auto;
        }
        .card {
            gap: 0px;
            font-size: 15px;
            display: inline-block;
            padding: 0;
            margin: 10px;
        }
        .card-blue {
            background-color: lightblue;
        }
        .card-red {
            background-color: lightcoral;
        }
        '''
    ),
    ui.panel_conditional(f"response.value.toUpperCase() !== '{response}'.toUpperCase()",
        ui.input_text("response", challenge, value=response)
    ),
    ui.panel_conditional(f"response.value.toUpperCase() === '{response}'.toUpperCase()",
 ui.navset_tab(
     ui.nav_panel("ROMANCER",
        ui.page_sidebar(
            ui.sidebar(
                ui.card(
                    {"class": "card card-blue"},
                    ui.div(
                        ui.p("Blue Temperament", style="font-weight: bold;"),
                        ui.input_slider("blue_response_threshold", "Response Threshold:", min=0, max=100, value=20),
                        ui.input_slider("blue_initial_pbf", "Initial PBF:", min=0, max=100, value=2),
                        ui.input_slider("blue_pbf_halflife", "PBF Halflife (days):", min=0, max=5, value=1),
                        ui.input_select("blue_amygdala", "Amygdala Archetype", choices=list(amygdala_choices.keys())),
                        ui.input_select("blue_ladder", "Escalation Ladder", choices=list(ladders.keys())),
                        class_="card-blue"
                    )
                ),
                ui.card(
                    {"class": "card card-red"},
                    ui.div(
                        ui.p("Red Temperament", style="font-weight: bold;"),
                        ui.input_slider("red_response_threshold", "Response Threshold:", min=0, max=100, value=70),
                        ui.input_slider("red_initial_pbf", "Initial PBF:", min=0, max=100, value=2),
                        ui.input_slider("red_pbf_halflife", "PBF Halflife (days):", min=0, max=3, value=1),
                        ui.input_select("red_amygdala", "Amygdala Archetype", choices=list(amygdala_choices.keys())),
                        ui.input_select("red_ladder", "Escalation Ladder", choices=list(ladders.keys())),
                        class_="card-red"
                    )
                )
            ),
            ui.div(
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
                ),
                class_="column-wrap"
            ),
            title="ROMANCER Hotline Demonstration",
            window_title="RAND Hotline",
        )
 ),
     ui.nav_panel("About",
                  ui.page_fluid(
                        ui.img(src=rand_svg_uri, style="width: 150px; margin: 30px;"),
                      ui.card(
                          ui.h1("RAND Ontological Model for Assessing Nuclear Crisis Escalation Risk"),
                          ui.p("aka, ROMANCER", style="font-weight: bold;"),
                          ui.h3("Introduction"),
                          ui.p('''
RAND Ontological Model for Assessing Nuclear Crisis Escalation Risk
(ROMANCER) is a model that represents nuclear escalation behaviours,
and includes multiple theories-of-mind that afford exploration of
decisionmakers taking actions, and making threats and demands, to see
how this might affect nuclear escalation outcomes.
'''),
                        ui.h3("About RAND"),
                          ui.p(
                        ui.HTML('''
RAND is a research organization that develops solutions to public policy challenges to
help make communities throughout the world safer and more secure, healthier and more prosperous.
RAND is nonprofit, nonpartisan, and committed to the public interest.
To learn more about RAND, visit <a href="http://www.rand.org">http://www.rand.org</a>
                        ''')
                          )

                      )
                  )
                  )
 )
     )
)

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
                    red_amyg=red_amygdala, red_ladder_file=red_ladder,
                    blue_initial_fight = 0.0, blue_initial_flight = 0.0, blue_initial_freeze = 0.0,
                    red_initial_fight = 0.0, red_initial_flight = 0.0, red_initial_freeze = 0.0
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
