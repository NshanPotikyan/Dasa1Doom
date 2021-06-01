import glob
import os
import utils as ut
import configs as cf


class Grader:

    def __init__(self, path, student_ids, mode='per_student', nr_problems=None):
        """
        Constructs the grader object
        :param path: str of the path to the jupyter notebook files
        :param student_ids: dict of the student ids
        :param mode: str of the checking mode ('per_student' or 'per_problem')
        :param nr_problems: int of the number of problems to be checked,
                            if None then it will be determined from one of the homework files
        """
        self.path = path
        self.student_ids = student_ids
        self.mode = mode

        self.files = glob.glob(f'{path}/*ipynb')
        assert len(self.files) > 0, "No files were found in the specified directory."
        self.nr_problems = nr_problems

        if mode == 'per_problem':
            if self.nr_problems is None:
                self.nr_problems = self.get_nr_problems()
        self.grade_dict = {}

    def grade(self):
        """
        Starts the grading process according to the grading mode (per problem or per student)
        :return:
        """
        if self.mode == 'per_student':
            return self.grade_per_student()
        elif self.mode == 'per_problem':
            return self.grade_per_problem()

    def grade_per_student(self):
        """
        Performs the grading per student
        :return:
        """

        # loop over all problems per person and store the results in the grade_dict
        for hw in self.files:
            # get student name from the file name (e.g. HW1_Loops_PoghosPoghosyan.ipynb)
            name = hw.split('_')[-1][:-6]

            assert name in self.student_ids, f"{name} student is not found"

            print(f'Processing {name}s homework')

            # open and read the notebook file
            notebook = ut.notebook_to_dict(file_name=hw)

            # we are interested in the cells
            cells = notebook['cells'].copy()
            nr_cells = len(cells)

            inserted_cells = 0
            total_grade = 0
            all_checked = True

            for i in range(nr_cells):
                cell = ut.join(cells[i]['source'])

                if not cell:
                    continue

                # checking if the cell contains the problem description
                # if starts with a number:
                if cell.strip()[0].isdigit():

                    # check if the problem is already graded
                    try:
                        grade_cell = ut.join(cells[i + 2]['source'])
                        if 'Grade' in grade_cell and 'Total' not in grade_cell:
                            total_grade += float(grade_cell.split(' ')[-1])
                            continue
                    except IndexError:
                        # handling the case when the last problem is not graded yet
                        pass

                    all_checked = False

                    # code will be in the next cell
                    code = ut.join(cells[i + 1]['source'])

                    grade, comment = self.get_grade_comment(cell, code)

                    if grade == 'ignore':
                        # the student's work will be ignored
                        continue

                    notebook = ut.insert_cell(notebook,
                                              position=i + inserted_cells + 2,
                                              content=grade,
                                              content_type='grade')
                    notebook = ut.insert_cell(notebook,
                                              position=i + inserted_cells + 3,
                                              content=comment,
                                              content_type='comment')

                    inserted_cells += 2
                    total_grade += float(grade)
                    ut.dict_to_notebook(some_dict=notebook,
                                        file_name=hw)

            self.grade_dict[name] = total_grade

            if not all_checked or 'Total' not in notebook['cells'][-1]:
                notebook = ut.insert_cell(notebook,
                                          position=len(notebook['cells']),
                                          content=str(total_grade),
                                          content_type='total_grade')
                ut.dict_to_notebook(some_dict=notebook,
                                    file_name=hw)
        self.grades_to_txt()

    def grade_per_problem(self):
        """
        Performs the grading per problem
        :return:
        """
        student_ids = self.student_ids

        # number of problems in the notebook
        nr_problems = self.nr_problems

        # loop over the same problem over all students

        # names of the students
        students = [i for i in student_ids.keys()]

        for i in range(1, nr_problems + 1):
            for j, student in enumerate(students):  # loop over each student
                print(f'Problem{i}-{student}')
                # open and read the hw
                hw = self.get_student_hw(student)
                if hw is None:
                    # no hw was submitted
                    self.grade_dict[student] = 0
                    continue

                notebook = ut.notebook_to_dict(hw)

                cells = notebook['cells'].copy()
                nr_cells = len(cells)

                # get all the cells in str format
                cells = [ut.join(cells[idx]['source']) for idx in range(nr_cells)]

                # get the index of the cell containing the i-th problem
                idx = self.get_ith_problem(cells=cells, problem_number=i)

                # check if the problem is already checked
                try:
                    grade_cell = cells[idx + 2]
                    if 'Grade' in grade_cell and 'Total' not in grade_cell:
                        grade = float(grade_cell.split(' ')[-1])
                        self.grade_dict[student] = self.grade_dict.get(student, 0) + grade
                        continue
                except IndexError:
                    # the case when it is the last problem that is not graded yet
                    pass

                cell = cells[idx]  # problem description
                code = cells[idx + 1]  # code from the student

                grade, comment = self.get_grade_comment(cell, code)

                if grade == 'ignore':
                    continue

                notebook = ut.insert_cell(notebook,
                                          position=idx + 2,
                                          content=grade,
                                          content_type='grade')
                notebook = ut.insert_cell(notebook,
                                          position=idx + 3,
                                          content=comment,
                                          content_type='comment')
                self.grade_dict[student] = self.grade_dict.get(student, 0) + float(grade)

                ut.dict_to_notebook(some_dict=notebook,
                                    file_name=hw)
        self.grades_to_txt()

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
            if cell.strip()[0].isdigit():
                counter += 0
        return counter

    def get_grade_comment(self, cell, code):
        """
        Primary function for  viewing the problem statement,
        executing the student's code, for assigning a grade
        and adding a comment
        :param cell: string of the text cell
        :param code: string of the code cell
        :return: tuple of strings
        """
        print(cell)
        print(code)
        grade = self._check_and_grade(code)
        comment = ''

        while True and grade != 'ignore':
            try:
                comment = self._provide_feedback(input('Enter a comment: '))
            except UnicodeDecodeError:
                # happens sometimes when commenting in Armenian
                comment = self._provide_feedback(input('Enter a comment: '))
            break
        return grade, comment


    @staticmethod
    def get_ith_problem(cells, problem_number):
        """
        Finds the cell of a particular problem with its index
        :param cells: list of notebook cells (str)
        :param problem_number: int of the problem index (starts from 1)
        :return: int of the cell index containing the requested problem
        """
        i = problem_number
        return [num for num in range(len(cells)) if cells[num].strip().startswith(f'{i}')][0]


    @staticmethod
    def _provide_feedback(comment):
        """
        This function is used to decode the comment
        e.g. add one of the default comments defined in the configs
        :param comment: str
        :return: str
        """
        if comment == '':
            return cf.default_comment
        comment = comment.replace('[solved]',
                                  cf.solved)
        return comment

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

    # def press_enter():
    #     """
    #     This function is used to take an input from the user
    #     :return: None if the input is 'quit' or 'stop', otherwise returns the input string
    #     """
    #     text = input('Press Enter to proceed: ')
    #     quitter(text)
    #     return text

    def _execute(self, repeat=False):
        """
        Controls the process of the code execution or providing the grade
        :param repeat: bool specifying whether we execute the code for the first time
                       or we repeat the execution
        :return: input string
        """
        disp_text = 'Press Enter to {} the code or Enter the grade to proceed: '
        if not repeat:
            disp_text = disp_text.format('execute')
        else:
            disp_text = disp_text.format('repeat')

        text = input(disp_text)
        self._quitter(text)

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

    def grades_to_txt(self):
        """
        Writing the total grades of the students to a .txt file
        :return:
        """
        with open(os.path.join(self.path, 'results.txt'), 'w') as f:
            for name, i in self.student_ids.items():
                f.write(f'{i}  {name}   {self.grade_dict.get(name, 0)}\n')

