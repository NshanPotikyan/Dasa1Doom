import json
import configs as cf


def join(text):
    """
    Helper function to join the strings in a list
    :param text: list of strings
    :returns: string
    """
    return ''.join(text)


def quitter(text):
    """
    This function is used to check if it is the time to terminate the program,
    that is when the user entered 'quit' or 'stop'
    :param text: string
    :return: None
    """
    text = text.strip().lower()
    if text == 'stop' or text == 'quit':
        quit()


def press_enter():
    """
    This function is used to take an input from the user
    :return: None if the input is 'quit' or 'stop', otherwise returns the input string
    """
    text = input('Press Enter to proceed: ')
    quitter(text)
    return text


def execute(repeat=False):
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
    quitter(text)

    if text != '' and text != 'ignore':
        try:
            float(text)
        except ValueError:
            print('Make sure you enter a valid grade: ')
            execute(repeat=repeat)
    return text


def check_and_grade(code):
    """
    Primary function for executing the student's code
    and for assigning a grade
    :param code: string of the code cell
    :return: string for the grade
    """
    if code.strip() == '':
        # if the code cell is empty
        return '0'
    grade = execute()
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
        grade = execute(repeat=True)
        if grade:
            return grade


def get_grade_comment(cell, code):
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
    grade = check_and_grade(code)
    comment = ''

    while True and grade != 'ignore':
        try:
            comment = provide_feedback(input('Enter a comment: '))
        except UnicodeDecodeError:
            # happens sometimes when commenting in Armenian
            comment = provide_feedback(input('Enter a comment: '))
        break
    return grade, comment


def notebook_to_dict(file_name):
    """
    Function for loading the jupyter notebook as a dict
    :param file_name: str of the .ipynb file name
    :return: dict
    """
    file = open(file_name, mode='r')
    return json.load(file)


def dict_to_notebook(some_dict, file_name):
    """
    Function for writing a jupyter notebook (JN) file (.ipynb)
    from a dict
    :param some_dict: dict that has a special format for JN files
    :param file_name: str of the JN file name
    :return:
    """
    with open(file_name, mode='w') as f:
        json.dump(some_dict, f)


def create_new_cell(content, content_type):
    """
    Generates a new text cell that will be added to the existing notebook
    :param content: str of the content that needs to be added
    :param content_type: str of the content type, currently it can be one of these
                         'grade', 'comment', 'total_grade'
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
        title = ''
        raise Exception(f"""The content_type was not specified correctly.
        Should be one of these 'grade', 'comment', 'total_grade', but {content_type}
        was provided.
        """)
    return {'cell_type': 'markdown',
            'metadata': {'id': ''},
            'source': [f'{title} {content}']}


def provide_feedback(comment):
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
