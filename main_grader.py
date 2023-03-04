import streamlit as st

from datetime import datetime

from graders import Grader

if __name__ == '__main__':
    # should be the folder on the server
    st.set_page_config(layout="wide", page_icon="", page_title="Homework Grader", )

    col1, col2 = st.columns(2)

    st.title("Homework Grader")

    st.sidebar.title("Files")

    uploaded_files = st.sidebar.file_uploader(
        "Upload the .ipynb files here",
        key="1",
        type='ipynb',
        accept_multiple_files=True,
        help="To activate 'wide mode', go to the hamburger menu > Settings > turn on 'wide mode'",
    )

    if not uploaded_files:
        st.info(
            f"""
                Upload the .ipynb files first.
                """
        )

        st.stop()
    else:
        # run the grader here
        st.sidebar.write("")
        grader = Grader(path=uploaded_files,
                        student_ids={
                            'AramAramyan': 1,
                            'ArmenAshotyan': 2
                        }, streamlit=True)
        grader.grade()

    # Insert comment
    with st.sidebar.expander("Add a comment"):
        form = st.form("comment")
        # name = form.selectbox('Name', COMMENTERS)
        comment = form.text_area("Comment")
        submit = form.form_submit_button("Add a comment")

        if submit:
            date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            st.success("☝️ Your comment was successfully posted.")

    st.sidebar.write("")

    tab1, tab2 = st.tabs(["Tab1", "Tab2", ])
