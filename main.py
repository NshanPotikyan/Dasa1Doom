from graders import Grader
import configs as cf

grader = Grader(path=cf.path, student_ids=cf.student_ids, mode=cf.mode, nr_problems=cf.nr_problems)
# print(grader.files)
grader.grade()

