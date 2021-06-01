import configs as cf

from graders import Grader

grader = Grader(path=cf.path, student_ids=cf.student_ids, mode=cf.mode, nr_problems=cf.nr_problems)
grader.grade()

