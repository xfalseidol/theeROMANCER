"""Interactive helper for sketching River Road wargame strategies.

This small, beginner-friendly CLI walks through a few prompts (or uses
defaults) to outline a scenario set around the Southeast Texas Highlands
and the river-bottom communities along River Road in Channelview, Texas.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable


@dataclass
class StrategyInputs:
    team_name: str
    objective: str
    terrain: str
    approach: str
    supply: str
    comms: str
    timeline: str
    risk: str
    fallback: str


DEFAULTS = {
    "team_name": "River Road Guardians",
    "objective": (
        "Protect barge traffic and nearby families while mapping escalation cues "
        "along the San Jacinto river bend"
    ),
    "terrain": (
        "Marshy river-bottom land between Lynchburg Ferry and Highlands with "
        "refinery stacks creating haze"
    ),
    "approach": "Low-profile scouts using jon boats and pickup spotters along River Road",
    "supply": "Stage fuel and first-aid at the Highlands bluff and Baytown boat ramp",
    "comms": "GMRS handhelds with a portable repeater on the Highlands water tower",
    "timeline": "First 30 minutes after an unexpected alert",
    "risk": "Watch flooding cuts, refinery security patrols, and civilian traffic on I-10",
    "fallback": "Pull back to the Highlands high ground and shift to river-crossing denial",
}


QUESTIONS: Iterable[tuple[str, str]] = (
    ("team_name", "Call sign or team nickname"),
    ("objective", "Primary objective for this run"),
    ("terrain", "How would you summarize the ground and waterways"),
    ("approach", "How do scouts move without escalating"),
    ("supply", "Where are you staging resupply and aid"),
    ("comms", "What comms plan keeps locals in the loop"),
    ("timeline", "What time window matters most"),
    ("risk", "Top risks you want to avoid"),
    ("fallback", "Fallback position if tension spikes"),
)


def _prompt_with_default(prompt: str, default: str, *, use_defaults: bool) -> str:
    if use_defaults:
        return default
    response = input(f"{prompt} [{default}]: ").strip()  # noqa: T201
    return response or default


def collect_inputs(use_defaults: bool = False) -> StrategyInputs:
    """Collect answers for the scenario, optionally using defaults."""
    answers = {}
    for key, prompt in QUESTIONS:
        answers[key] = _prompt_with_default(prompt, DEFAULTS[key], use_defaults=use_defaults)
    return StrategyInputs(**answers)


def format_summary(inputs: StrategyInputs) -> str:
    """Build a short text brief for the River Road scenario."""
    lines = [
        "=== River Road Wargame Brief ===",
        "Setting: Southeast Texas Highlands and San Jacinto river-bottom communities along River Road in Channelview.",
        f"Team: {inputs.team_name}",
        f"Objective: {inputs.objective}",
        f"Terrain notes: {inputs.terrain}",
        f"Approach: {inputs.approach}",
        f"Supply plan: {inputs.supply}",
        f"Comms: {inputs.comms}",
        f"Timeline: {inputs.timeline}",
        f"Risks to avoid: {inputs.risk}",
        f"Fallback: {inputs.fallback}",
        "Use these notes to seed ROMANCER cases or as a quick-start for tabletop discussion.",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> str:
    parser = argparse.ArgumentParser(
        description=(
            "Guided CLI for a Southeast Texas River Road escalation vignette. "
            "Press Enter to accept defaults or pass --accept-defaults to skip prompts."
        )
    )
    parser.add_argument(
        "--accept-defaults",
        action="store_true",
        help="Skip questions and use the beginner defaults.",
    )
    args = parser.parse_args(argv)

    inputs = collect_inputs(use_defaults=args.accept_defaults)
    summary = format_summary(inputs)
    print(summary)  # noqa: T201
    return summary


if __name__ == "__main__":
    main()
