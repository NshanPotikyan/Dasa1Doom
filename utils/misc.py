import os
import glob
import pandas as pd


def remove_difference(dict_before, dict_after):
    # TODO: remove keys that are in dict_after, but not in dict_before
    keys_to_remove = set(dict_after) - set(dict_before)
    for key in keys_to_remove:
        del globals()[key]


def grades2dict(path, file_name='results.txt', to_csv=False):
    """
    Collects the grades from txt file into a dict and
    optionally creates a csv file of (id, grade) pairs.

    :param str path: directory of the txt file
    :param str file_name: name of the txt file
    :param bool to_csv: specifies whether to save the csv file
    :returns: name to grades mapping
    :rtype: dict
    """
    file = os.path.join(path, file_name)
    if not os.path.exists(file):
        raise FileNotFoundError(file)
    grades = pd.read_csv(os.path.join(path, file_name),
                         header=None,
                         sep='  ')
    if to_csv:
        import warnings
        warnings.filterwarnings('ignore')

        grades_csv = grades.copy()
        grades_csv[2][grades_csv[2] == -1] = 0
        grades_csv.loc[:, [0, 2]].to_csv(
            os.path.join(path, file_name.replace('.txt', '.csv')), index=False)

    return dict(zip(grades[1], grades[2]))


def get_student_info(students, emails=False):
    """
    Collects students to ids mapping, or optionally students to emails mapping.

    :param dict or str students: either the final dict is provided, or path to the csv file
        that contains 0 (Ids), 1 (Names) or 0 (Ids), 1 (Names), 2 (Emails) columns
    :param bool emails: specifies whether we want to get the students to emails mapping
    :returns:
    :rtype: dict
    """
    if isinstance(students, dict):
        return students
    elif isinstance(students, str):
        # in case we provide a csv file with Ids, Names columns
        student_data = pd.read_csv(students, header=None)
        if emails:
            return dict(zip(student_data[1], student_data[2]))
        return dict(zip(student_data[1], student_data[0]))


def get_files(path, file_type='ipynb'):
    """
    Reads all the file paths of given extension.

    :param str path: directory of interest where the submission folders are stored
    :param str file_type: the type of files we want to get paths for
    :returns: dictionary of student name and file path pairs
    :rtype: dict
    """
    student2file = {}
    for folder in os.listdir(path):
        student_name = folder.split('_')[0]
        student2file[student_name] = glob.glob(os.path.join(path, folder, f'*{file_type}'))[0]
    return student2file


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


def get_grade(text):
    import streamlit as st

    # with st.sidebar.expander("Add a comment"):
    form = st.form(text)
    grade = form.number_input('Grade', min_value=0, max_value=1)
    # comment = form.text_area("Comment")
    submit = form.form_submit_button("Add a comment")
    if submit:
        return grade


def remove_symbols(name):
    return ''.join([i for i in name if i.isalpha()])


def read_txt(path, file_name):
    """
    Reads a txt file.

    :param str path: directory of the file
    :param str file_name: name ending with .txt
    :return: file content
    :rtype: str
    """
    with open(os.path.join(path, file_name)) as f:
        return f.read()


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


def find_in_dict(some_dict, key):
    """
    Searches for key occurrences (approximate) in the given dict and
    returns the matched keys.

    :param dict[str, Any] some_dict:
    :param str key: string of interest
    :returns:
    :rtype: list[str]
    """

    key = key.lower()
    out = []
    for k in some_dict:
        if key in k.lower():
            out.append(k)
    return out


def keep_letters(some_str):
    """Keeps only the letters in a string."""
    return ''.join(filter(str.isalpha, some_str))
