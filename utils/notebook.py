import os
import json

import utils.misc as um


def join(text):
    """
    Helper function to join the strings in a list

    :param list[str] text:
    :returns:
    :rtype: str
    """
    return ''.join(text)


def notebook_to_dict(file_name):
    """
    Function for loading the jupyter notebook as a dict

    :param str file_name: .ipynb file name
    :return: dict
    """
    if isinstance(file_name, str):
        file_name = open(file_name, mode='r', encoding="utf8")
    return json.load(file_name)


def dict_to_notebook(some_dict, file_name):
    """
    Function for writing a jupyter notebook (JN) file (.ipynb)
    from a dict
    :param dict some_dict: has a special format for JN files
    :param str file_name: JN file name
    :return:
    """
    if not isinstance(file_name, str):
        # case of streamlit
        file_name = file_name.name
    with open(file_name, mode='w') as f:
        json.dump(some_dict, f)


def get_cell_id(cells, some_text):
    """
    Finds the cell id that starts with the given text.

    :param cells: list of notebook cells (str)
    :param str some_text: text of interest
    :return: int of the cell index containing the requested problem
    """
    return [num for num in range(len(cells)) if cell_startswith(cell=cells[num],
                                                                some_text=some_text)][0]


def cell_startswith(cell, some_text):
    """Checks if the cell starts with the given string.

    :param str cell: notebook cell
    :param str some_text: text of interest
    :return: bool
    """
    cell = cell.strip()
    if cell:
        return cell.startswith(f'{some_text}')
    return False


def save_notebook(save_dir, file_name, file_dict, update=False, files=None):
    """
    Saves notebook and optionally updates the files.

    :param list[str] files: notebook file names
    :param str save_dir: directory to save the graded notebooks in
    :param str file_name: .ipynb notebook file name
    :param dict file_dict: notebook content as dict
    :param bool update: specifies whether to update the files
        so that if some problems are already graded they are skipped later
    :returns: notebook file names optionally updated
    :rtype: list[str]
    """
    new_file_name = os.path.join(save_dir, os.path.basename(file_name))
    dict_to_notebook(file_name=new_file_name, some_dict=file_dict)
    if update:
        assert files, "in case update=True, files should be provided."
        # used for grading after detecting plagiarism
        files[files.index(file_name)] = new_file_name
    return files


def find_cell_id_per_notebook(files, file_name, some_text=None):
    """
    Processes the notebook file and returns the id of the cell
    that starts with the given condition.

    :param list[str] files: file paths
    :param str file_name: name of the .ipynb file
    :param str some_text: text of interest
    :returns: hw - file name
            notebook - dict of the notebook read from json
            cells - list of str containing the necessary parts of the notebook
            idx - int of the index of the problem code in the notebook
    :rtype: tuple
    """
    file_name = um.get_file(files=files, file_name=file_name, letter_tolerance=1)

    if file_name is None:
        return [None] * 4

    notebook = notebook_to_dict(file_name)

    cells = notebook['cells'].copy()
    nr_cells = len(cells)

    if some_text is None:
        # get all code cells
        return '\n'.join([join(cells[idx]['source']) for idx in range(nr_cells) if cells[idx]['cell_type'] == 'code'])
    else:
        # get all the cells in str format
        cells = [join(cells[idx]['source']) for idx in range(nr_cells)]

    # get the index of the cell containing the i-th problem
    try:
        idx = get_cell_id(cells=cells, some_text=some_text)
    except IndexError:
        raise Exception(f'{some_text} was not found.\
         Make sure you search the correct text.')
    return file_name, notebook, cells, idx


def display_notebook_cell(cell):
    import streamlit as st
    import base64

    if cell['cell_type'] == 'code':
        st.code(join(cell['source']))
        for output in cell['outputs']:
            if 'text' in output:
                st.info(join(output['text']))
            elif 'data' in output:
                if 'image/png' in output['data']:
                    st.image(base64.b64decode(output['data']['image/png']))
                else:
                    if 'text/html' in output['data']:
                        table = output['data']['text/html']
                        idx = len(table)
                        if '    <div class="colab-df-buttons">\n' in table:
                            idx = table.index('    <div class="colab-df-buttons">\n')
                        st.markdown(join(table[:idx]), unsafe_allow_html=True)

    else:
        st.markdown(join(cell['source']), unsafe_allow_html=True)
