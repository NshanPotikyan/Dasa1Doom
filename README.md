# Homework Grader

This repository contains scripts which I use to semi-automate the homework grading process of the programming course that I teach.

## Quick Start

1. First make sure you have the jupyter notebook files stored in
 a single directory and each file contains the student names in the following format: ``"something_NameSurname.ipynb"``. 
 You can see sample files [here](https://github.com/NshanPotikyan/HomeworkGrader/tree/master/sample_homeworks). 

2. Open the [``configs.py``](https://github.com/NshanPotikyan/HomeworkGrader/blob/master/configs.py) file and
 fill it in accordingly. 
 
3. After completing the config file you can run the following script to start grading each student's work:

```bash
python main.py
``` 

4. You can pass some of the configs directly to the script, for example:

```bash
python main.py --path=sample_homeworks --mode=per_problem --nr_problems=2
```

5. After going over all problems and grading them, 
you will see a .txt file with the aggregated grades and each .ipynb file will contain the grades and 
comments that were provided by the user.

6. If you want to terminate the grading process, you can type ``stop`` or ``quit`` as an input.

7. If you want to ignore a problem (leave it ungraded), you can type ``ignore``.

## Homework Format

Currently the code works for jupyter notebook files of the following structure:

```markdown
Some cells that do not contain problem statements (do not start with a number)

1. Problem statement (Text Cell)

Code for the problem (Code Cell)

2. Problem statement (Text Cell)

Code for the second problem (Code Cell)

...

```

## TODO

In future I will try to add the following features:

* Check homeworks by running assertion blocks

* Dynamically save comments (feedbacks) and enable fast insertion of frequent comments

* Detect potential plagiarism using unsupervised learning techniques, such as clustering.
