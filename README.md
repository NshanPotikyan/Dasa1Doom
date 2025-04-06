# Dasa1Doom

This repository contains scripts which I use to semi-automate the grading process of the programming courses that I teach.

## Homework Grader

First, you need to install the dependencies:

```commandline
pip install -r requirements.txt
```

### Quick Start

1. To detect plagiarism
```commandline
streamlit run detect_plagiarism.py -- --path path_to_submissions --plagiarism_tol_level 0.9
```

2. To grade the submissions
```commandline
streamlit run grader.py -- --path path_to_submissions
```
