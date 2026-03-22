from romancer.river_road_cli import DEFAULTS, collect_inputs, format_summary, main


def test_collect_inputs_uses_defaults():
    answers = collect_inputs(use_defaults=True)
    assert answers.team_name == DEFAULTS["team_name"]
    assert answers.fallback == DEFAULTS["fallback"]


def test_main_accept_defaults_outputs_context(capsys):
    summary = main(["--accept-defaults"])
    captured = capsys.readouterr().out
    for needle in (
        "River Road",
        "Channelview",
        DEFAULTS["team_name"],
    ):
        assert needle in captured
        assert needle in summary


def test_format_summary_mentions_river_bottom():
    answers = collect_inputs(use_defaults=True)
    summary = format_summary(answers)
    assert "river-bottom" in summary
