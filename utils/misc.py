import numpy as np
import json
import matplotlib.pyplot as plt

from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

from utils.code_similarity import detect, summarize


def normalize_dict(some_dict, values_sum=100):
    """
    Converts the values of a dict, such that the values sum up to the provided scalar (defaults to 100).

    :param dict some_dict: dict with scalar values
    :param int values_sum: the desired amount that the final dict values should sum up to
    :returns:
    :rtype: dict
    """
    total_sum = sum(some_dict.values())
    return {k: round(v / total_sum * values_sum, 2) for k, v in some_dict.items()}


def append_tab(some_str):
    out = '\n\t'.join(some_str.split('\n'))
    return f'\t{out}\n'


def get_grade(text):
    import streamlit as st

    # with st.sidebar.expander("Add a comment"):
    form = st.form(text)
    grade = form.number_input('Grade', min_value=0, max_value=1)
    # comment = form.text_area("Comment")
    submit = form.form_submit_button("Add a comment")
    if submit:
        return grade


def join(text):
    """
    Helper function to join the strings in a list
    :param text: list of strings
    :returns: string
    """
    return ''.join(text)


def notebook_to_dict(file_name):
    """
    Function for loading the jupyter notebook as a dict
    :param file_name: str of the .ipynb file name
    :return: dict
    """
    if isinstance(file_name, str):
        file_name = open(file_name, mode='r', encoding="utf8")
    return json.load(file_name)


def get_student_name(file_name):
    if not isinstance(file_name, str):
        # the case of streamlit
        file_name = file_name.name
    return file_name.split('_')[-1][:-6]


def dict_to_notebook(some_dict, file_name):
    """
    Function for writing a jupyter notebook (JN) file (.ipynb)
    from a dict
    :param some_dict: dict that has a special format for JN files
    :param file_name: str of the JN file name
    :return:
    """
    if not isinstance(file_name, str):
        # case of streamlit
        file_name = file_name.name
    with open(file_name, mode='w') as f:
        json.dump(some_dict, f)


def insert_cell(notebook, position, content, content_type):
    """
    Inserts a new text cell inside the given notebook
    :param notebook: dict of the JN file
    :param position: int of the cell positional index
    :param content: str of the content that needs to be added
    :param content_type: str of the content type, currently it can be one of these
                         'grade', 'comment', 'total_grade'
    :return: dict of the modified JN file
    """
    notebook['cells'].insert(position,
                             create_new_cell(content=content,
                                             content_type=content_type))
    return notebook


def create_new_cell(content, content_type):
    """
    Generates a new text cell that will be added to the existing notebook
    :param content: str of the content that needs to be added
    :param content_type: str of the content type, currently it can be one of these
                         'grade', 'comment', 'total_grade', 'empty'
    :return:
    """
    if content_type == 'grade':
        title = "<font color='red'>**Grade:**</font>"
    elif content_type == 'empty':
        title = ""
        content = ""
    elif content_type == 'comment':
        title = "<font color='red'>**Comment:**</font>"
    elif content_type == 'total_grade':
        title = "<font color='red'>**Total Grade:**</font>"
    else:
        raise Exception(f"""The content_type was not specified correctly.
        Should be one of these 'grade', 'comment', 'total_grade', 'empty', but {content_type}
        was provided.
        """)
    return {'cell_type': 'markdown',
            'metadata': {'id': ''},
            'source': [f'{title} {content}']}


def hamming_dist(str1, str2):
    """
    Calculates the hamming distance between two strings
    :param str1:
    :param str2:
    :return: float
    """
    dist = 0
    for i in range(len(str1)):
        dist += (str2[i] != str1[i]) * 1
    return dist


def detect_summarize(pycode_list, names, tolerance_level=0.9):
    """
    Goes over all code strings and looks for potential plagiarism
    :param pycode_list: list of str containing python code
    :param names: list of str containing student names
    :param tolerance_level: float of the plagiarism tolerance level
    :return:
    """
    nr_codes = len(pycode_list)
    similarity_matrix = np.ones((nr_codes, nr_codes))
    cheaters = []
    for i in range(nr_codes):
        try:
            results = detect(pycode_list[i:], keep_prints=True, module_level=True)
        except SyntaxError:
            continue
        for index, func_ast_diff_list in results:
            sum_plagiarism_percent, _, _ = summarize(func_ast_diff_list)
            similarity_matrix[i, index + i] = round(sum_plagiarism_percent, 2)
            if sum_plagiarism_percent > tolerance_level:
                print('{:.2f} % of {} code structure is similar with {} code structure.'.format(
                    sum_plagiarism_percent * 100, names[i], names[index + i]))
                print(names[i], pycode_list[i], sep='\n****\n')
                print(names[i + index], pycode_list[i + index], sep='\n****\n')
                penalize = input('Do you want to penalize for plagiarism? Yes(1) or No(2)')
                if penalize:
                    cheaters.append([names[i], names[i + index]])

    # make the similarity matrix symmetric
    i_lower = np.tril_indices(nr_codes, -1)
    similarity_matrix[i_lower] = similarity_matrix.T[i_lower]
    return cheaters, similarity_matrix


def plot_dendrogram(matrix, labels=None, title='', color_threshold=0.3, linkage_type='single'):
    """
    Plot the dendrogram of the clustering
    :param matrix: numpy array of similarity matrix
    :param labels: list of str for leaf names
    :param title: str of the plot title
    :param color_threshold: float for coloring the tree linkages as clusters, below the specified value
    :param linkage_type: str type of linkage to apply (see sklearn documentation for more info)
    :return:
    """
    if labels is None:
        labels = [f'{i}' for i in np.arange(len(matrix))]
    dists = squareform(matrix)
    linkage_matrix = linkage(dists, linkage_type)
    plt.figure(figsize=(15, 10))
    dendrogram(linkage_matrix, color_threshold=color_threshold,
               labels=labels, show_contracted=True, leaf_rotation=30)
    plt.ylabel('Dissimilarity')
    plt.title(f'{title}')
    plt.savefig(f'{title}.jpg')
