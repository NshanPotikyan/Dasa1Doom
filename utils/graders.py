import glob
import os
import numpy as np
import pandas as pd
from tqdm import tqdm

import utils.misc as ut
from configs import general as cf
from utils.assertion_parser import AssertionParser


class Grader:

    def __init__(self, path=None,
                 student_ids=None,
                 mode='per_student',
                 nr_problems=None,
                 with_assertions=False,
                 points=None,
                 hidden_assertions=None,
                 save_comments=False,
                 detect_plagiarism=False,
                 plagiarism_tol_level=0.9,
                 save_dendrograms=False,
                 save_dir='graded',
                 streamlit=False):
        """
        Constructs the grader object
        :param path: str of the path to the jupyter notebook files
        :param student_ids: dict of the student ids
        :param mode: str of the checking mode ('per_student' or 'per_problem')
        :param nr_problems: int of the number of problems to be checked,
                            if None then it will be determined from one of the homework files
        :param with_assertions: bool specifying whether the problems contain assertions or not
        :param points: dict of absolute scores of each problem
        :param hidden_assertions: dict of the assertions
        :param save_comments: bool specifying whether you want to use comment suggestions or not
        :param detect_plagiarism: bool specifying whether you want to detect potential plagiarism or not
        :param plagiarism_tol_level: float between 0 and 1 for the plagiarism tolerance level
        :param save_dendrograms: bool specifying whether to save dendrogram plots or not
        """
        self.path = path
        self.student_ids = self._get_student_ids(student_ids)
        self.mode = mode
        self.with_assertions = with_assertions
        self.assertion_parser = AssertionParser(hidden_assertions=hidden_assertions)
        self.hidden_assertions = hidden_assertions
        self.save_comments = save_comments
        self.comments = None
        self.detect_plagiarism = detect_plagiarism
        self.plagiarism_tol_level = plagiarism_tol_level
        self.students = [i for i in self.student_ids.keys()]
        self.save_dendrograms = save_dendrograms
        self.streamlit = streamlit

        if isinstance(path, str):
            save_dir = os.path.join(self.path, save_dir)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            self.save_dir = save_dir

            self.files = glob.glob(os.path.join(f'{path}', '*ipynb'))
        else:
            # in case of uploaded files (streamlit)
            self.files = path

        assert len(self.files) > 0, "No files were found in the specified directory."

        if nr_problems is None:
            self.nr_problems = self.get_nr_problems()

        self.points = self._get_points_dict(points)

        self.grade_dict = {}

    @staticmethod
    def _get_student_ids(students):
        if isinstance(students, dict):
            return students
        elif isinstance(students, str):
            # in case we provide a csv file with Ids, Names columns
            student_data = pd.read_csv(students, header=None)
            return dict(zip(student_data[1], student_data[0]))

    def _save_graded(self, file_name, file_dict):
        file_name = os.path.join(self.save_dir, os.path.basename(file_name))
        ut.dict_to_notebook(file_name=file_name, some_dict=file_dict)

    def _get_points_dict(self, points):
        """
        Creates a dictionary for absolute points of each assignment.

        :param str or None or dict points: in case points='stars', then the point for each assignment will
            be determined given the amount of stars,
            in case points=None, then the points will be entered by
            the grader during the grading, in case a dict is provided, then that will be the absolute points
        :returns:
        :rtype: dict
        """
        if points == 'stars':
            # take one hw file
            notebook = ut.notebook_to_dict(file_name=self.files[0])
            cells = notebook['cells']
            nr_cells = len(cells)
            points_dict = {}
            problem_number = 1
            for i in range(nr_cells):
                cell = ut.join(cells[i]['source'])
                if self._contains_ith_problem_statement(cell, i=problem_number):
                    points_dict[problem_number] = cell.count('⭐')
                    problem_number += 1
                if problem_number > self.nr_problems:
                    break
            points_dict = ut.normalize_dict(points_dict)
            return points_dict
        return {} if points is None else points

    def grade(self):
        """
        Starts the grading process according to the grading mode (per problem or per student)
        :return:
        """
        if self.detect_plagiarism:
            self.search_plagiarism_and_penalize()

        if self.mode == 'per_student':
            return self.grade_per_student()
        elif self.mode == 'per_problem':
            return self.grade_per_problem()

    def grade_per_student(self):
        """
        Performs the grading per student
        :return:
        """

        if self.save_comments:
            self.comments = {}

        # loop over all problems per person and store the results in the grade_dict
        for hw in tqdm(self.files):
            # get student name from the file name (e.g. HW1_Loops_PoghosPoghosyan.ipynb)
            name = ut.get_student_name(file_name=hw)

            assert name in self.student_ids, f"{name} student is not found"

            self.show(f'Processing {name}s homework')

            # open and read the notebook file
            notebook = ut.notebook_to_dict(file_name=hw)

            # we are interested in the cells
            cells = notebook['cells'].copy()
            nr_cells = len(cells)

            inserted_cells = 0
            total_grade = 0
            all_checked = True
            problem_nr = 0

            for i in range(nr_cells):
                cell = ut.join(cells[i]['source'])

                if not cell:
                    continue

                # checking if the cell contains the problem description
                # if starts with a number:
                if self._contains_problem_statement(cell):

                    problem_nr += 1

                    # check if the problem is already graded
                    try:
                        grade_cell = ut.join(cells[i + 2 + self.with_assertions]['source'])
                        if cf.grade_title in grade_cell and cf.total_grade_title not in grade_cell:
                            total_grade += float(grade_cell.split(' ')[-1])
                            if self.save_comments:
                                comment_cell = ut.join(cells[i + 3 + self.with_assertions]['source'])
                                self.comments[problem_nr] = self.comments.get(problem_nr, '') + \
                                                            comment_cell.split('</font> ')[-1] + '\n'
                            continue
                    except IndexError:
                        # handling the case when the last problem is not graded yet
                        pass

                    all_checked = False

                    # code will be in the next cell
                    code = ut.join(cells[i + 1]['source'])

                    grade, comment = self.get_grade_comment(cell, code, problem_nr)

                    if grade == 'ignore':
                        # the student's work will be ignored
                        continue

                    # from relative to absolute grade
                    grade = self._rel2abs_grade(grade, problem_nr=problem_nr)

                    notebook = ut.insert_cell(notebook,
                                              position=i + inserted_cells + 2 + self.with_assertions,
                                              content=grade,
                                              content_type='grade')
                    notebook = ut.insert_cell(notebook,
                                              position=i + inserted_cells + 3 + self.with_assertions,
                                              content=comment,
                                              content_type='comment')
                    if self.save_comments:
                        self.comments[problem_nr] = self.comments.get(problem_nr, '') + comment + '\n'

                    inserted_cells += 2
                    total_grade += grade
                    self._save_graded(file_dict=notebook, file_name=hw)

            total_grade = round(total_grade)
            self.grade_dict[name] = total_grade

            if not all_checked or cf.total_grade_title not in notebook['cells'][-1]:
                notebook = ut.insert_cell(notebook,
                                          position=len(notebook['cells']),
                                          content=total_grade,
                                          content_type='total_grade')
                self._save_graded(file_dict=notebook, file_name=hw)

        self.grades_to_txt()

    def grade_per_problem(self):
        """
        Performs the grading per problem
        :return:
        """
        # number of problems in the notebook
        nr_problems = self.nr_problems

        if self.save_comments:
            self.comments = {}

        # loop over the same problem over all students

        for i in range(1, nr_problems + 1):

            for j, student in enumerate(self.students):  # loop over each student
                print(f'Problem{i}-{student}')
                hw, notebook, cells, idx = self.find_problem_per_student(student, problem_id=i)

                if hw is None:
                    # no hw was submitted
                    self.grade_dict[student] = 0
                    continue

                # check if the problem is already checked
                try:
                    grade_cell = cells[idx + 2]
                    if cf.grade_title in grade_cell and cf.total_grade_title not in grade_cell:
                        grade = float(grade_cell.split(' ')[-1])
                        self.grade_dict[student] = self.grade_dict.get(student, 0) + grade
                        if self.save_comments:
                            comment_cell = cells[idx + 3]
                            self.comments[i] = self.comments.get(i, '') + comment_cell.split('</font> ')[-1] + '\n'
                        continue
                except IndexError:
                    # the case when it is the last problem that is not graded yet
                    pass

                cell = cells[idx]  # problem description
                code = cells[idx + 1]  # code from the student

                grade, comment = self.get_grade_comment(cell, code, i)

                if grade == 'ignore':
                    continue

                # from relative to absolute grade
                grade = self._rel2abs_grade(grade, problem_nr=i)

                notebook = ut.insert_cell(notebook,
                                          position=idx + 2 + self.with_assertions,
                                          content=grade,
                                          content_type='grade')
                notebook = ut.insert_cell(notebook,
                                          position=idx + 3 + self.with_assertions,
                                          content=comment,
                                          content_type='comment')
                if self.save_comments:
                    self.comments[i] = self.comments.get(i, '') + comment + '\n'

                self.grade_dict[student] = self.grade_dict.get(student, 0) + float(grade)

                self._save_graded(file_dict=notebook, file_name=hw)

        self.grades_to_txt()

    def find_problem_per_student(self, student, problem_id):
        """
        Opens the notebook file for the given student
        :param student: str of student name
        :param problem_id: int of the problem number
        :return:
        hw - file name
        notebook - dict of the notebook read from json
        cells - list of str containing the necessary parts of the notebook
        idx - int of the index of the problem code in the notebook
        """
        hw = self.get_student_hw(student)

        if hw is None:
            return [None] * 4

        notebook = ut.notebook_to_dict(hw)

        cells = notebook['cells'].copy()
        nr_cells = len(cells)

        # get all the cells in str format
        cells = [ut.join(cells[idx]['source']) for idx in range(nr_cells)]

        # get the index of the cell containing the i-th problem
        try:
            idx = self.get_ith_problem(cells=cells, problem_number=problem_id)
        except IndexError:
            raise Exception(f'Problem {problem_id} was not found.\
             Make sure the total number of problems was set correctly.')
        return hw, notebook, cells, idx

    def search_plagiarism_and_penalize(self):
        """
        Goes over all the problems for each student
        searches for potential plagiarism, asks the user to double check the detection
        and penalizes if needed
        :return:
        """
        similarity_tensor = []
        for i in range(1, self.nr_problems + 1):
            codes = []
            names = []

            for j, student in enumerate(self.students):
                _, _, cells, idx = self.find_problem_per_student(student, problem_id=i)

                if idx is None:
                    continue

                codes.append(cells[idx + 1])
                names.append(student)

            cheaters, similarity_matrix = ut.detect_summarize(codes, names,
                                                              tolerance_level=self.plagiarism_tol_level)
            diss_matrix = 1 - similarity_matrix

            if self.save_dendrograms:
                ut.plot_dendrogram(matrix=diss_matrix, labels=names, title=f'Problem {i}')

            similarity_tensor.append(diss_matrix)

            for students in cheaters:
                self.penalize(students, problem_id=i)

        if self.save_dendrograms:
            similarity_tensor = np.array(similarity_tensor)
            mean_similarity = similarity_tensor.mean(axis=0)
            ut.plot_dendrogram(mean_similarity, labels=names, title='Over All Problems')

    def penalize(self, student_names, problem_id):
        """
        Set the grade and comment of those students who have cheated
        :param student_names: list of strings for student names
        :param problem_id: int of the problem number
        :return:
        """
        for student_name in student_names:
            hw, notebook, cells, idx = self.find_problem_per_student(student_name,
                                                                     problem_id=problem_id)

            notebook = ut.insert_cell(notebook,
                                      position=idx + 2,
                                      content=0,
                                      content_type='grade')
            notebook = ut.insert_cell(notebook,
                                      position=idx + 3,
                                      content=cf.plagiarism_comment,
                                      content_type='comment')

            self._save_graded(file_dict=notebook, file_name=hw)

    def get_student_hw(self, student_name, letter_tolerance=2):
        """
        Finds the student's homework by tolerating spelling errors in the file name
        :param student_name: str of the student name
        :param letter_tolerance: int of the number of letters that can be misspelled
        :return:
        """
        similarity = 10
        for idx, file in enumerate(self.files):
            if student_name in file:
                return file
            name = file[-len(student_name):]
            current_similarity = ut.hamming_dist(student_name, name)
            if current_similarity < similarity:
                similarity = current_similarity
                best_idx = idx
        if similarity <= letter_tolerance:
            return self.files[best_idx]
        else:
            print(f"{student_name}'s homework was not found, \
            please make sure the file name was written correctly otherwise \
            the hw is considered not submitted.")
            return None

    def get_nr_problems(self):
        """
        Finds the number of problems in the notebook
        :return: int
        """
        notebook = ut.notebook_to_dict(file_name=self.files[0])
        cells = notebook['cells']
        nr_cells = len(cells)
        counter = 0
        for i in range(nr_cells):
            cell = ut.join(cells[i]['source'])
            if self._contains_problem_statement(cell):
                counter += 1
        return counter

    def get_grade_comment(self, cell, code, problem_nr):
        """
        Get the grade and the comment/feedback for the given problem,
        if there is an exception during the code execution, then the problem
        will be graded manually and
        if the homework does not contain assertions then again the process will
        be supervised by the grader
        :param cell: str of the problem statement
        :param code: str of the code block
        :param problem_nr: int of the problem number
        :return:
        """
        if self.with_assertions:
            try:
                grade, comment = self.assertion_parser(problem_id=problem_nr,
                                                       code_cell=code)
            except Exception as e:
                print(e)

                grade, comment = self._get_grade_comment_without_assertions(code, problem_nr)
            return grade, comment
        self.show(cell)

        return self._get_grade_comment_without_assertions(code, problem_nr)

    def _rel2abs_grade(self, grade, problem_nr):
        """
        Transforms the relative grade [0, 1] to absolute grade
        using the defined total points for the given problem
        :param grade: str or float of the grade
        :param problem_nr: int of the problem number
        :return: float of the grade
        """
        grade = float(grade)
        grade *= self.points.get(problem_nr, 1)
        return round(grade, 2)

    def _get_grade_comment_without_assertions(self, code, problem_nr):
        """
        Primary function for  viewing the problem statement,
        executing the student's code, for assigning a grade
        and adding a comment
        :param code: string of the code cell
        :param problem_nr: int of the problem number
        :return: tuple of strings
        """
        self.show(code, code=True)
        grade = self._check_and_grade(code)
        comment = ''

        disp_text = self._enter_comment(problem_nr)

        while True and grade != 'ignore':
            try:
                comment = self._provide_feedback(disp_text)
            except UnicodeDecodeError:
                # happens sometimes when commenting in Armenian
                comment = self._provide_feedback(disp_text)
            break
        return grade, comment

    def _enter_comment(self, problem_nr):
        """
        Constructs the string for the comment input display
        :param problem_nr: int of the problem number
        :return: str of the display text
        """
        disp_text = 'Enter a comment: \n'

        if self.save_comments:
            disp_text += 'It can be one of these: \n'
            comments = self.comments[problem_nr]
            unique_comments = set(comments.split('\n'))
            i = 0
            for comment in unique_comments:
                if comment:
                    disp_text += f'{i + 1}) {comment}\n'
                    i += 1
        return disp_text

    def get_ith_problem(self, cells, problem_number):
        """
        Finds the cell of a particular problem with its index
        :param cells: list of notebook cells (str)
        :param problem_number: int of the problem index (starts from 1)
        :return: int of the cell index containing the requested problem
        """
        i = problem_number
        return [num for num in range(len(cells)) if self._contains_ith_problem_statement(cell=cells[num], i=i)][0]

    def grades_to_txt(self):
        """
        Writing the total grades of the students to a .txt file
        :return:
        """
        with open(os.path.join(self.path, 'results.txt'), 'w') as f:
            for name, i in self.student_ids.items():
                f.write(f'{i}  {name}   {self.grade_dict.get(name, 0)}\n')

    def _execute(self, repeat=False):
        """
        Controls the process of the code execution or providing the grade
        :param repeat: bool specifying whether we execute the code for the first time
                       or we repeat the execution
        :return: input string
        """
        disp_text = 'Press Enter to {} the code or Enter the grade (relative) to proceed: '
        if not repeat:
            disp_text = disp_text.format('execute')
        else:
            disp_text = disp_text.format('repeat')

        text = self._get_input(disp_text)

        if text != '' and text != 'ignore':
            try:
                float(text)
            except ValueError:
                print('Make sure you enter a valid grade: ')
                self._execute(repeat=repeat)
        return text

    def _check_and_grade(self, code):
        """
        Primary function for executing the student's code
        and for assigning a grade
        :param code: string of the code cell
        :return: string for the grade
        """
        if code.strip() == '':
            # if the code cell is empty
            return '0'
        grade = self._execute()
        if grade:
            return grade
        while True:
            # this part is for code testing and grading
            # when the user pressed Enter
            try:
                exec(code, globals())
            except SyntaxError:
                # the case when the code cell is missing
                # below the problem statement
                raise Exception(f"""
                The following cell does not contain code or it has syntax error in it:
                {code}
                """)
            grade = self._execute(repeat=True)
            if grade:
                return grade

    def _get_input(self, disp_text):
        """
        Enables the user to enter an input.
        The program finishes if the input is 'quit' or 'stop'
        :param disp_text:
        :return:
        """
        # TODO: add feature for adding a comment from streamlit
        if self.streamlit:
            text = ut.get_grade(disp_text)
        else:
            text = input(disp_text)
            self._quitter(text)
        return text

    def _provide_feedback(self, disp_text):
        """
        This function is used to decode the comment
        e.g. add one of the default comments defined in the configs
        or select one of the previously entered comments
        :param disp_text: str
        :return: str
        """

        comment = self._get_input(disp_text)

        if comment == '':
            return cf.default_comment

        comment = comment.replace('[solved]',
                                  cf.solved)

        if self.save_comments:
            if comment.isdigit():
                for com in disp_text.split('\n'):
                    if com.startswith(comment):
                        comment = com.split(') ')[-1]
        return comment

    def show(self, *args, **kwargs):
        if self.streamlit:
            import streamlit as st

            if kwargs.get('code', False):
                st.code(*args)
            else:
                st.write(*args)
        else:
            print(*args)

    @staticmethod
    def _quitter(text):
        """
        This function is used to check if it is the time to terminate the program,
        that is when the user entered 'quit' or 'stop'
        :param text: string
        :return: None
        """
        text = text.strip().lower()
        if text == 'stop' or text == 'quit':
            quit()

    @staticmethod
    def _contains_problem_statement(cell):
        """Checks if the cell contains the problem description

        :param cell: str for notebook cell
        :return: bool
        """
        if cell:
            return cell[0].isdigit() or cell.strip().startswith(cf.problem_starts_with)
        return False

    @staticmethod
    def _contains_ith_problem_statement(cell, i):
        """Checks if the cell contains the ith problem description

        :param cell: str for notebook cell
        :param i: int for the problem index
        :return: bool
        """
        cell = cell.strip()
        return cell.startswith(f'{i}') or cell.startswith(f'{cf.problem_starts_with}{i}')
