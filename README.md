# RAND Ontological Model for Assessing Nuclear Crisis Escalation Risk (ROMANCER)


## Introduction

RAND Ontological Model for Assessing Nuclear Crisis Escalation Risk
(ROMANCER) is a model that represents nuclear escalation behaviours,
and includes multiple theories-of-mind that afford exploration of
decisionmakers taking actions, and making threats and demands, to see
how this might affect nuclear escalation outcomes.

ROMANCER is implemented in Python; basic usage does not require extreme
familiarity with Python, but it is anticipated that users, developers,
and researchers will need to be able to program Python to get the most
out of this model.

## Quick Start

To quickly see ROMANCER play out a basic scenario, create a Python
virtual environment, then run the "hotline" demo. The virtual environment
only needs to be created once, then the demos can be run many times:

**Create Virtual Environment**
```sh
# Create venv:
python3 -m venv venv
# On Linux/Mac, Activate venv:
source venv/bin/activate
# On Windows, Activate venv:
venv\Scripts\activate.bat
# Install required python modules
python3 -m pip install -r requirements.txt
```

**Run Model**
```sh
# venv must be activated [activate per instructions above] to run model
# Change into demo directory
cd demo/hotline
# Run model
python3 ./hotline_demo_gui.py
# Several charts will be created in the current directory as output
```

## References

(Insert reference for RR- research report, and TL- analyst guide, available on http://www.rand.org)


## Developers

**Lead Researcher**: Edward Geist <egeist@rand.org>  
**Developers**: Nancy Huerta <nhuerta@rand.org>, Gary Briggs <gbriggs@rand.org>

