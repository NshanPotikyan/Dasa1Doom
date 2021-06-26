import argparse
import configs as cf

from graders import Grader

parser = argparse.ArgumentParser(description="Homework checking.")

parser.add_argument('--path', default=None,
                    help="The path to the jupyter notebook files.")
parser.add_argument('--mode', default=None,
                    help="The grading mode, supports either 'per_problem' or 'per_student' grading")
parser.add_argument('--nr_problems', type=int, default=None,
                    help="The number of problems to be checked, \
                     if None, then the number of problems will be determined automatically from one of the files.")
parser.add_argument('--with_assertions', type=bool, default=None,
                    help="If True, then each problem should have assertion blocks (public and private) and \
                     the grading will be based on the outcomes of the assertions.")
parser.add_argument('--save_comments', type=bool, default=None,
                    help="If True, then there will be comment recommendation based on previous comments.")
parser.add_argument('--detect_plagiarism', type=bool, default=None,
                    help="If True, then the codes will be analyzed for potential plagiarism.")
parser.add_argument('--plagiarism_tol_level', type=float, default=None,
                    help="Float between 0 and 1 for the plagiarism tolerance level.")
parser.add_argument('--save_dendrograms', type=bool, default=None,
                    help="If True, then the dendrogram plot of cheating clusters will be saved.")


args = parser.parse_args()

if __name__ == "__main__":
    if args.path:
        path = args.path
    else:
        path = cf.path

    if args.mode:
        mode = args.mode
    else:
        mode = cf.mode

    if args.nr_problems:
        nr_problems = args.nr_problems
    else:
        nr_problems = cf.nr_problems

    if args.with_assertions:
        import sys
        sys.path.append(cf.path)
        from assertions import hidden_assertions
        with_assertions = args.with_assertions
    else:
        with_assertions = cf.with_assertions
        hidden_assertions = None

    if args.detect_plagiarism:
        detect_plagiarism = args.detect_plagiarism
    else:
        detect_plagiarism = cf.detect_plagiarism

    if args.plagiarism_tol_level:
        plagiarism_tol_level = args.plagiarism_tol_level
    else:
        plagiarism_tol_level = cf.plagiarism_tol_level

    if args.save_dendrograms:
        save_dendrograms = args.save_dendrograms
    else:
        save_dendrograms = cf.save_dendrograms

    grader = Grader(path=path, student_ids=cf.student_ids, mode=mode,
                    nr_problems=nr_problems, with_assertions=with_assertions,
                    points=cf.points, hidden_assertions=hidden_assertions,
                    save_comments=args.save_comments, detect_plagiarism=detect_plagiarism,
                    plagiarism_tol_level=plagiarism_tol_level, save_dendrograms=save_dendrograms)
    grader.grade()

