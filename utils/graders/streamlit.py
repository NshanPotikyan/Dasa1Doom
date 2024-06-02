import streamlit as st
import base64

import utils.notebook as un
import utils.misc as um


class GraderStreamlit:
    def __init__(self, path):
        self.path = path

    def grade(self):
        files = um.get_files(path=self.path, file_type='ipynb')
        students = [um.get_student_name(file) for file in files]
        self.run(files=files, students=students)

    def run(self, files, students):
        st.set_page_config(layout="wide", page_icon="", page_title="Grader", )

        st.title("Homework Grader")

        all_notebooks = [self.get_notebook(files, student) for student in students]

        nr_notebooks = len(all_notebooks)

        if 'idx' not in st.session_state:
            st.session_state.idx = 0

        hw = all_notebooks[st.session_state.idx]

        if st.button('Display'):
            st.info(students[st.session_state.idx])

            for i, cell in enumerate(hw):

                if cell['cell_type'] == 'code':
                    st.code(un.join(cell['source']))
                    for output in cell['outputs']:
                        if 'text' in output:
                            st.info(un.join(output['text']))
                        elif 'data' in output:
                            st.image(base64.b64decode(output['data']['image/png']))

                else:
                    st.markdown(un.join(cell['source']), unsafe_allow_html=True)

        if st.session_state.idx == nr_notebooks - 1:

            if st.button("Finish", key="finish"):
                st.success('The job is completed.')
                st.stop()

        if st.button("Next", key="next"):

            if st.session_state.idx < nr_notebooks - 1:
                st.session_state.idx += 1

    @staticmethod
    def get_notebook(files, file_name):
        file_name = um.get_file(files=files,
                                file_name=file_name,
                                letter_tolerance=1)

        if file_name is None:
            return None

        notebook = un.notebook_to_dict(file_name)

        return notebook['cells'].copy()
