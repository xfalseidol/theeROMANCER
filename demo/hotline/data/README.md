# Hotline Ladder Data

## Introduction

ROMANCER's "hotline" demo simulates a *Cuban Missile Crisis*-like scenario.

In this scenario, each actor has their own Escalation Ladder
representation. Actors can have different ladders. The files in here
describe the ladders.

## Inputs

Input files are all in the form of CSV files, easily editable using Excel.

In each file, any line whose first cell is blank is treated as a comment.

### Top-level Ladder Input

The top level file is loaded first, its purpose is to point to the other
input files.

Only the columns ```input``` and ```filename``` are important,
```description``` is only a comment.

The first column is used by the model to find the other files, so when
creating new files, ensure that the values are the same as provided in
the sample.

In several of the inputs, a ```side``` is included. Those are actor
names, but may optionally be "Self" and "Adversary", in which case they
are remapped to the appropriate actors, when loaded. This facilitates
symmetric ladders on both actors, without needing to duplicate input files.

### Action Lexicon

This file describes the actions available in the scenario. It is important
that both red and blue ladders have exactly the same action lexicon.

### Ladder Description

This is a map of rung number, to cosmetic name. This is the file that
the model relies on for number of rungs in the escalation ladder; if
subsequent files reference rung numbers that are not contained in this
file, those subsequent input records are ignored.

The rung numbers are important; number them from 1 to n. The name of
each rung has no semantic meaning to the model, and is used primarily
in visualisation.

### Matching Rules

Each matching rule starts with a rung, and has various actions in it.
If any action listed for a given rung is taken, then that rung is among
the ones an actor may move to. Typically, actors will move to the highest
rung that was matched when making a move.

### Rung Change Actions

These are actions that are taken around changing rungs.

When an actor moves to a higher rung than they are currently at, then
they take all the actions listed as "action", for that new rung.

When an actor wishes to de-escalate, they take the "deescalate" actions
for the rung they are currently at, and after their adversary next acts
they may de-escalate to a lower rung.

More details are in ```romancer/agent/escalation_logic.md```

