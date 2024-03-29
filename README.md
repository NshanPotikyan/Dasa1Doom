# Dasa1Doom

This repository contains scripts which I use to semi-automate the grading process of the programming courses that I teach.

## Homework Grader

### Quick Start

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
python main.py --path=sample_homeworks/without_assertions --mode=per_problem --nr_problems=2
```

5. If you want to save and then reuse inserted comments, you can run the following:

```bash
python main.py --path=sample_homeworks/without_assertions \
               --mode=per_problem --nr_problems=2 \
               --save_comments=True
```

In this case, you will see suggested comments with their respective ids and in order to choose 
any of them, just enter the corresponding comment id. 

6. If you want to **detect plagiarism** and penalize for it you can set the configs 
related to plagiarism inside the ``configs.py`` and/or run the following script:

```bash
python main.py --path=sample_homeworks/without_assertions \
               --mode=per_problem --save_comments=True \
               --detect_plagiarism=True --plagiarism_tol_level=0.9
```

In this case you will need to double check the code of those students that 
had similar (above 90% similarity) solutions and decide whether you want to penalize 
for plagiarism or not.

7. Additionally, you can generate dendrogram plots to detect potential clusters of
cheating students by adding the ``--save_dendrograms=True`` flag:

```bash
python main.py --path=sample_homeworks/without_assertions \
               --mode=per_problem --save_comments=True \
               --detect_plagiarism=True --plagiarism_tol_level=0.9 \
               --save_dendrograms=True
```

You will notice problem-level, as well as aggregated (averaged over all problems)
dendrogram images in your current directory.


8. After going over all problems and grading them, 
you will see a .txt file with the aggregated grades and each .ipynb file will contain the grades and 
comments that were provided by the user.

9. If you want to terminate the grading process, you can type ``stop`` or ``quit`` as an input.

10. If you want to ignore a problem (leave it ungraded), you can type ``ignore``.



### Homework Format

There are two major types of homeworks that can be graded using this tool:

### Homeworks Without Tests (Assertions)
In this case each problem is graded by looking at the problem description, code,
 code execution results and then inserting the grade and comment (feedback).

Currently the code works for jupyter notebook files of the following structure:

```markdown
Some cells that do not contain problem statements (do not start with a number)

1. Problem statement (Text Cell)

Code for the problem (Code Cell)

2. Problem statement (Text Cell)

Code for the second problem (Code Cell)

...

```

### Homeworks With Tests (Assertions)

In case each problem has its own assertions, you can create a separate ``assertions.py`` file
 and include the assertions in a dictionary, as in this example 
 [file](https://github.com/NshanPotikyan/HomeworkGrader/blob/master/sample_homeworks/with_assertions/assertions.py).
To start grading you can run this:

```bash
python main.py --path=sample_homeworks/with_assertions \
               --mode=per_problem --nr_problems=5 \
               --with_assertions=True
```

* if the code cells in the notebook do not raise any exceptions, then the above code will take care 
of the whole grading process, including the failed assertions in the student's comments/feedback

* if the code cells in the notebook raise an exception, then the grader will need to grade that problem manually
as in the case of "*Homeworks Without Tests (Assertions)*" 

## Important notes

* The grader should provide relative grades and the absolute grade will be
 calculated based on the ``points`` dictionary defined in the 
 [``configs.py``](https://github.com/NshanPotikyan/HomeworkGrader/blob/master/configs.py)

* If some problems are already graded (there is a **Grade**, **Comment** cell below the code cell), then 
the program skips grading that problem automatically


# TODO

In future, I will try to add the following features:

- [x] Check homeworks by running assertion blocks automatically (fully unsupervised)

- [x] Dynamically save comments (feedbacks) and enable fast insertion of frequent comments

- [x] Detect potential plagiarism using [pycode_similar](https://github.com/fyrestone/pycode_similar)

- [x] Generate a dendrogram of students to detect potential clusters of cheating students

- [x] Add Kahoot report parser

- [ ] Create a minimal GUI 
