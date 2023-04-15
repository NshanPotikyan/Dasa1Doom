import argparse
from tqdm import tqdm

import utils.misc as um
from configs import students as sc
from utils.messenger import Messenger

parser = argparse.ArgumentParser(description="Homework checking.")

parser.add_argument('--path', default='sample_homeworks/hw1/graded_',
                    help="The path to the graded jupyter notebook files.")
parser.add_argument('--subject',
                    help="Email subject.")
parser.add_argument('--student_ids', type=str, help="path to the csv file that contains students names, emails.")


args = parser.parse_args()

if __name__ == '__main__':
    path = args.path
    subject = args.subject
    assert subject, "The subject should be provided"
    # student ids, names, grades
    students2grades = um.grades2dict(path=path, to_csv=True)
    students2emails = um.get_student_info(args.student_ids, emails=True)
    students2ids = um.get_student_info(args.student_ids, emails=False)
    notebooks = um.get_files(path, 'ipynb')
    students2notebooks = {um.get_student_name(v): v for v in notebooks}

    message = um.read_txt(path, 'message.txt')
    messenger = Messenger(send_from='nshan.potikyan@gmail.com',
                          send_from_name='Նշան Փոթիկյան',
                          subject=subject)

    for student, grade in tqdm(students2grades.items()):
        if grade < 0:
            # the case of not submitting the HW
            continue
        student_email = students2emails[student]
        try:
            messenger(send_to=student_email,
                      message=message.format(subject=subject,
                                             id=students2ids[student]),
                      files=students2notebooks[student])
        except:
            print(f'Email was not sent successfully to {student_email}.')
