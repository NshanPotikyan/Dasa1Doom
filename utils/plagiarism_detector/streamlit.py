import streamlit as st
import os

import utils.notebook as un
import utils.misc as um

from utils.code_similarity import detect, summarize


class PlagiarismDetectorStreamlit:
    skip_commands = ['pip', 'unzip', 'wget']
    """
    :param str path: defines the directory where the notebooks are
    :param float tol_level: the sensitivity/confidence of the detection
    """
    files = None
    students = None

    def __init__(self,
                 path,
                 tol_level=0.9,
                 ):
        self.path = path
        self.tol_level = tol_level

    def detect(self):
        student2file = um.get_files(path=self.path, file_type='ipynb')
        # students = [um.get_student_name(file) for file in files]
        self.run(student2file)

    def run(self, student2file):
        """
        Goes over all the problems for each student
        searches for potential plagiarism, asks the user to double check the detection
        and penalizes if needed
        :return:
        """
        st.set_page_config(layout="wide", page_icon="", page_title="Plagiarism Detector", )

        st.title("Plagiarism Detector")

        pycode_list, cells, names = self.get_codes_names(student2file)

        nr_codes = len(pycode_list)
        candidates = []
        for i in range(nr_codes):
            try:
                results = detect(pycode_list[i:], keep_prints=True, module_level=True)
            except SyntaxError as e:
                print(e, 'Check the code, maybe there are bash commands.')
                continue
            for index, func_ast_diff_list in results:
                sum_plagiarism_percent, _, _ = summarize(func_ast_diff_list)
                if sum_plagiarism_percent > self.tol_level:
                    candidates.append({
                        'code1': pycode_list[i],
                        'notebook1': cells[i],
                        'notebook2': cells[i + index],
                        'code2': pycode_list[i + index],
                        'name1': names[i],
                        'name2': names[i + index],
                        'score': sum_plagiarism_percent,
                    })

        if 'idx' not in st.session_state:
            st.session_state.idx = 0
            st.session_state.cheaters = []

        if len(candidates) == 0:
            st.success('No cheaters were found.')
            st.stop()

        c1, c2 = st.columns(2)
        pair = candidates[st.session_state.idx]

        if st.button('Display'):
            with c1:
                st.info(pair['name1'])
                for cell in pair['notebook1']:
                    un.display_notebook_cell(cell)

            with c2:
                st.info(pair['name2'])
                for cell in pair['notebook2']:
                    un.display_notebook_cell(cell)

        if st.session_state.idx == len(candidates) - 1:

            if st.button("Penalize", key="penalize2"):
                st.session_state.cheaters.append([pair['name1'], pair['name2']])

            if st.button("Finish", key="finish"):
                st.success('The job is completed.')
                st.info(f'{st.session_state.cheaters}')

                with open(os.path.join(self.path, 'cheaters.txt'), 'w') as f:
                    f.write(f'{st.session_state.cheaters}')

                st.stop()

        if st.button("Penalize", key="penalize"):
            st.session_state.cheaters.append([pair['name1'], pair['name2']])

            if st.session_state.idx < len(candidates) - 1:
                st.session_state.idx += 1

        if st.button("Skip", key="skip"):
            if st.session_state.idx < len(candidates) - 1:
                st.session_state.idx += 1

    @staticmethod
    def get_code_per_problem(file_name, skip_commands):

        notebook = un.notebook_to_dict(file_name)

        cells = notebook['cells'].copy()
        nr_cells = len(cells)

        code = []
        skip = False
        for idx in range(nr_cells):
            if cells[idx]['cell_type'] == 'code':
                for skip_command in skip_commands:
                    if any([skip_command in c for c in cells[idx]['source']]):
                        skip = True
                if skip:
                    continue
                code.append(un.join(cells[idx]['source']))

        code = '\n'.join(code)

        return code, cells

    def get_codes_names(self, student2file):
        codes = []
        names = []
        cells = []

        for student in student2file:
            code, cell = self.get_code_per_problem(file_name=student2file[student],
                                                   skip_commands=self.skip_commands)

            if code is None:
                continue

            codes.append(code)
            cells.append(cell)
            names.append(student)
        return codes, cells, names
