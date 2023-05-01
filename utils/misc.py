import os
import glob
import pandas as pd


def remove_difference(dict_before, dict_after):
    # TODO: remove keys that are in dict_after, but not in dict_before
    keys_to_remove = set(dict_after) - set(dict_before)
    for key in keys_to_remove:
        del globals()[key]


def get_file(files, file_name, letter_tolerance=0):
    """
    Finds the file by tolerating spelling errors in the file name
    :param list[str] files:
    :param str file_name: file name
    :param letter_tolerance: int of the number of letters that can be misspelled
    :return:
    """
    if not letter_tolerance:
        # in case we do not care aboust spelling errors
        return files[files.index(file_name)]

    similarity = 10
    for idx, file in enumerate(files):
        if file_name in file:
            return file
        name = file[-len(file_name):]
        current_similarity = hamming_dist(file_name, name)
        if current_similarity < similarity:
            similarity = current_similarity
            best_idx = idx
    if similarity <= letter_tolerance:
        return files[best_idx]
    else:
        print(f"{file_name}'s file was not found, \
        please make sure the file name was written correctly otherwise \
        the file is considered not submitted.")
        return None


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

    :param str path: directory of interest
    :param str file_type: the type of files we want to get paths for
    :returns:
    :rtype: list
    """
    return glob.glob(os.path.join(f'{path}', f'*{file_type}'))


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


def get_student_name(file_name):
    """
    Parses student name from file name.

    :param str file_name: should be of the following format something_name.ipynb
    :returns: student name
    :rtype: str
    """
    if not isinstance(file_name, str):
        # the case of streamlit
        file_name = file_name.name

    file_name = os.path.basename(file_name)
    nr_underscores = file_name.count('_')
    splits = file_name.split('_')
    if nr_underscores <= 2:
        # in case namesurname.ipynb or name-surname.ipynb
        return remove_symbols(splits[-1][:-6])
    elif nr_underscores == 3:
        # in case name_surname.ipynb
        return splits[-2] + splits[-1][:-6]


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
