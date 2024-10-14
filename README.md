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

This work was commissioned by AFGSC A5/8 and was conducted in Project
AIR FORCE's Strategy and Doctrine Program.

## Quick Start

To quickly see ROMANCER play out a basic scenario, create a Python
virtual environment, then run the "hotline" demo. The virtual environment
only needs to be created once, then the demos can be run many times:

ROMANCER has been tested on Linux and Windows x64.

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

```bibtex
@techreport{rand2024a2673_2,
  author      = "Jim Mignano, Gary J. Briggs, Nancy Huerta, Edward Geist, Dahlia Anne Goldfeld",
  title       = "The RAND Ontological Model for Assessing Nuclear Crisis Escalation Risk (ROMANCER) User Guide for Version 1.0",
  institution = "RAND",
  year        = "2024",
  type        = "Draft Tool",
  number      = "A2673-2",
  month       = "October",
}
```

```bibtex
@techreport{rand2024a2673_3,
  author      = "Edward Geist, Dahlia Goldfeld, Gary Briggs, Nancy Huerta, Jim Mignano, and Nina Miller",
  title       = "The RAND Ontological Model for Assessing Nuclear Crisis Escalation Risk (ROMANCER) Theoretical Introduction and Background",
  institution = "RAND",
  year        = "2024",
  type        = "Draft Report",
  number      = "A2673-3",
  month       = "October",
}
```

## About RAND

RAND is a research organization that develops solutions to public policy
challenges to help make communities throughout the world safer and more
secure, healthier and more prosperous.  RAND is nonprofit, nonpartisan,
and committed to the public interest. To learn more about RAND, visit
http://www.rand.org

RAND Project AIR FORCE (PAF), a division of RAND, is the Department of the
Air Force’s (DAF’s) federally funded research and development center
for studies and analyses, supporting both the United States Air Force
and the United States Space Force. PAF provides the DAF with independent
analyses of policy alternatives affecting the development, employment,
combat readiness, and support of current and future air, space, and cyber
forces. Research is conducted in four programs: Strategy and Doctrine;
Force Modernization and Employment; Resource Management; and Workforce,
Development, and Health.

## License

This code is Copyright (C) 2024 RAND Corporation, and provided under
the MIT license


## Developers

**Lead Researcher**: Edward Geist <egeist@rand.org>  
**Developers**: Nancy Huerta <nhuerta@rand.org>, Gary Briggs <gbriggs@rand.org>

