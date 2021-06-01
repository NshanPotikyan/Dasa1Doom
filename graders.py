import glob
import utils as ut
import os


class Grader:

    def __init__(self, path, student_ids, mode='per_student', nr_problems=None):
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
        if self.mode == 'per_student':
            return self.grade_per_student()
        elif self.mode == 'per_problem':
            return self.grade_per_problem()

    def grades_to_txt(self):
        with open(os.path.join(self.path, 'results.txt'), 'w') as f:
            for name, i in self.student_ids.items():
                f.write(f'{i}  {name}   {self.grade_dict.get(name, 0)}\n')

    def grade_per_student(self):

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
                # if 'Problem' in cell or starts with a number:
                if cell[0].isdigit() or cell.startswith('Problem'):

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

                    grade, comment = ut.get_grade_comment(cell, code)

                    if grade == 'ignore':
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
        student_ids = self.student_ids
        nr_problems = self.nr_problems

        # loop over the same problems over all students
        # number of problems in the notebook

        # file_name = ut.get_hw_name(path)

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
                # hw = f'{file_name}{student}.ipynb'
                #
                # assert os.path.exists(hw), f"{hw} file is not found"

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

                grade, comment = ut.get_grade_comment(cell, code)

                # print(grade == 'add_code_cell')

                if grade == 'check_next_cell':
                    # avoiding IndexError
                    if len(cells) > idx + 2:
                        if cells[idx+2] != '' or not cells[idx+2].strip()[0].isdigit():
                            grade, comment = ut.get_grade_comment(cell, cells[idx+2])
                        else:
                            grade, comment = 0, ''
                    else:
                        grade, comment = 0, ''
                elif grade == 'add_code_cell':
                    notebook = ut.insert_cell(notebook,
                                              position=idx + 1,
                                              content="",
                                              content_type='empty')
                    grade = 0

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

    def get_student_hw(self, student_name):
        similarity = 10
        for idx, file in enumerate(self.files):
            if student_name in file:
                return file
            name = file[-len(student_name):]
            current_similarity = ut.hamming_dist(student_name, name)
            if current_similarity < similarity:
                similarity = current_similarity
                best_idx = idx
        if similarity < 2:
            return self.files[best_idx]
        else:
            return None
        # raise Exception(f"{student_name}'s homework was not found, \
        # please make sure the file name was written correctly.")

    @staticmethod
    def get_ith_problem(cells, problem_number):
        i = problem_number
        return [num for num in range(len(cells)) if f'Problem{i}' in cells[num] or cells[num].strip().startswith(f'{i}')][0]

    def get_nr_problems(self):
        notebook = ut.notebook_to_dict(file_name=self.files[0])
        cells = notebook['cells']
        nr_cells = len(cells)
        counter = 0
        for i in range(nr_cells):
            cell = ut.join(cells[i]['source'])
            if cell[0].isdigit() or cell.startswith('Problem'):
                counter += 0
        return counter

