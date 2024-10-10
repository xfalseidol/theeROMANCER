# ROMANCER Demos

## Introduction

ROMANCER is generally intended to be used programmatically, for easier
integration into other models and general versatility.

This folder contains some self-complete demonstrations of ROMANCER use.

## Included Demos

### CommandPE

CommandPE is a model whose mission-level output can be used for an
interesting ROMANCER demonstration.

It is a one-player game: ROMANCER is reading "here's what happened during
a scenario" and modeling a decision-maker's view on escalation during
that scenario.

Most scenarios analysed using ROMANCER are not commonly avaialble at the
unclassified level, so a python tool that simulates a minimal scenario
playout, and outputs data in a format that should be similar to 
CommandPE output.

### Hotline

This is a two-player game. High level decision makers are at opposite
ends of a telephone. Each is sending messages to the other, then both
sides escalation posture is simulated.

This demo comes with a desktop GUI app to experiment with,
called ```hotline_demo_gui.py```. It also comes with a shiny GUI.
Please see ```shiny_requirements.txt``` for deployment instructions.

