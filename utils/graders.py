import os
from tqdm import tqdm

from configs import general as cf
import utils.notebook as un
import utils.misc as um


class Grader:

    def __init__(self, path=None,
                 student_ids=None,
                 mode='per_student',
                 nr_problems=None,
                 with_assertions=False,
                 points=None,
                 assertion_parser=None,
                 save_comments=False,
                 plagiarism_detector=None,
                 save_dir='graded',
                 streamlit=False):
        """
        Constructs the grader object
        :param str or None path: path to the jupyter notebook files
        :param dict or None student_ids: student ids
        :param str mode: the grading mode ('per_student' or 'per_problem')
        :param int or None nr_problems: int of the number of problems to be checked,
                            if None then it will be determined from one of the homework files
        :param bool with_assertions: specifying whether the problems contain assertions or not
        :param dict or None points: absolute scores of each problem, if None, then it will be inferred from the file
        :param bool save_comments: specifying whether you want to use comment suggestions or not, applicable when
            with_assertions=False
        :param plagiarism_detector:
        :param assertion_parser:
        :param bool streamlit: whether to run the grader with GUI
        :param str save_dir: folder name for the graded notebooks to be saved in
        """
        self.path = path
        self.student_ids = um.get_student_info(student_ids)
        self.mode = mode
        self.with_assertions = with_assertions
        self.assertion_parser = assertion_parser
        self.plagiarism_detector = plagiarism_detector
        self.save_comments = save_comments
        self.comments = None
        self.students = [i for i in self.student_ids.keys()]
        self.streamlit = streamlit

        if isinstance(path, str):
            save_dir = os.path.join(self.path, save_dir)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            self.save_dir = save_dir

            self.files = um.get_files(path=path, file_type='ipynb')
        else:
            # in case of uploaded files (streamlit)
            self.files = path

        assert len(self.files) > 0, "No files were found in the specified directory."

        if nr_problems is None:
            self.nr_problems = self.get_nr_problems()

        self.points = self._get_points_dict(points)

        self.grade_dict = {}

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
            notebook = un.notebook_to_dict(file_name=self.files[0])
            cells = notebook['cells']
            nr_cells = len(cells)
            points_dict = {}
            problem_number = 1
            for i in range(nr_cells):
                cell = un.join(cells[i]['source'])
                if un.cell_startswith(cell=cell,
                                      some_text=f'{cf.problem_starts_with}{problem_number}'):
                    points_dict[problem_number] = cell.count('⭐')
                    problem_number += 1
                if problem_number > self.nr_problems:
                    break
            points_dict = um.normalize_dict(points_dict)
            return points_dict
        return {} if points is None else points

    def grade(self):
        """
        Starts the grading process according to the grading mode (per problem or per student)
        :return:
        """
        if self.plagiarism_detector:
            # TODO: check this part
            self.plagiarism_detector(files=self.files, students=self.students)

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
            student = um.get_student_name(file_name=hw)

            if student not in self.student_ids:
                self.show(f"{student} student is not found")

            # self.show(f'Processing {name}s homework')

            # open and read the notebook file
            notebook = un.notebook_to_dict(file_name=hw)

            # we are interested in the cells
            cells = notebook['cells'].copy()
            nr_cells = len(cells)

            inserted_cells = 0
            all_checked = True
            problem_nr = 0

            for i in range(nr_cells):
                cell = un.join(cells[i]['source'])

                if not cell:
                    continue

                # checking if the cell contains the problem description
                # if starts with a number:
                if un.cell_startswith(cell=cell, some_text=cf.problem_starts_with):

                    problem_nr += 1

                    # check if the problem is already graded
                    try:

                        grade_cell = un.join(cells[i + 2 + self.with_assertions]['source'])
                        if cf.grade_title in grade_cell and cf.total_grade_title not in grade_cell:
                            grade = float(grade_cell.split(' ')[-1])
                            self.grade_dict[student] = self.grade_dict.get(student, 0) + grade

                            if self.save_comments:
                                comment_cell = un.join(cells[i + 3 + self.with_assertions]['source'])
                                self.comments[problem_nr] = self.comments.get(problem_nr, '') + \
                                                            comment_cell.split('</font> ')[-1] + '\n'
                            continue
                    except IndexError:
                        # handling the case when the last problem is not graded yet
                        pass

                    all_checked = False

                    # code will be in the next cell
                    code = un.join(cells[i + 1]['source'])

                    grade, comment = self.get_grade_comment(cell, code, problem_nr)

                    if grade == 'ignore':
                        # the student's work will be ignored
                        continue

                    # from relative to absolute grade
                    grade = self._rel2abs_grade(grade, problem_nr=problem_nr)

                    notebook = un.insert_cell(notebook,
                                              position=i + inserted_cells + 2 + self.with_assertions,
                                              content=grade,
                                              content_type='grade')
                    notebook = un.insert_cell(notebook,
                                              position=i + inserted_cells + 3 + self.with_assertions,
                                              content=comment,
                                              content_type='comment')
                    if self.save_comments:
                        self.comments[problem_nr] = self.comments.get(problem_nr, '') + comment + '\n'

                    inserted_cells += 2

                    self.grade_dict[student] = self.grade_dict.get(student, 0) + float(grade)

                    un.save_notebook(save_dir=self.save_dir, file_dict=notebook, file_name=hw)

            if not all_checked or cf.total_grade_title not in notebook['cells'][-1]:
                notebook = un.insert_cell(notebook,
                                          position=len(notebook['cells']),
                                          content=self.grade_dict.get(student, 0),
                                          content_type='total_grade')
                un.save_notebook(file_dict=notebook, file_name=hw, save_dir=self.save_dir)

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

        for problem_nr in range(1, nr_problems + 1):

            for j, student in enumerate(self.students):  # loop over each student
                # print(f'Problem{i}-{student}')
                hw, notebook, cells, idx = un.find_cell_id_per_notebook(
                    files=self.files,
                    file_name=student,
                    some_text=f'{cf.problem_starts_with}{problem_nr}')

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
                            self.comments[problem_nr] = self.comments.get(problem_nr, '') + \
                                                        comment_cell.split('</font> ')[-1] + '\n'
                        continue
                except IndexError:
                    # the case when it is the last problem that is not graded yet
                    pass

                cell = cells[idx]  # problem description
                code = cells[idx + 1]  # code from the student

                grade, comment = self.get_grade_comment(cell, code, problem_nr)

                if grade == 'ignore':
                    continue

                # from relative to absolute grade
                grade = self._rel2abs_grade(grade, problem_nr=problem_nr)

                notebook = un.insert_cell(notebook,
                                          position=idx + 2 + self.with_assertions,
                                          content=grade,
                                          content_type='grade')
                notebook = un.insert_cell(notebook,
                                          position=idx + 3 + self.with_assertions,
                                          content=comment,
                                          content_type='comment')
                if self.save_comments:
                    self.comments[problem_nr] = self.comments.get(problem_nr, '') + comment + '\n'

                self.grade_dict[student] = self.grade_dict.get(student, 0) + float(grade)

                un.save_notebook(file_dict=notebook, file_name=hw, save_dir=self.save_dir)

        self.grades_to_txt()

    def get_nr_problems(self):
        """
        Finds the number of problems in the notebook
        :return: int
        """
        notebook = un.notebook_to_dict(file_name=self.files[0])
        cells = notebook['cells']
        nr_cells = len(cells)
        counter = 0
        for i in range(nr_cells):
            cell = un.join(cells[i]['source'])
            if un.cell_startswith(cell=cell, some_text=cf.problem_starts_with):
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

    def grades_to_txt(self):
        """
        Writing the total grades of the students to a .txt file
        :return:
        """
        with open(os.path.join(self.save_dir, 'results.txt'), 'w') as f:
            for name, i in self.student_ids.items():
                f.write(f'{i}  {name}   {self.grade_dict.get(name, -1)}\n')

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
            text = um.get_grade(disp_text)
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
