import argparse
from configs import general as cf
from utils.graders import Grader
from utils.assertion_parser import AssertionParser
from utils.plagiarism_detector import PlagiarismDetector

parser = argparse.ArgumentParser(description="Homework checking.")

parser.add_argument('--path', default='sample_homeworks/with_assertions',
                    help="The path to the jupyter notebook files.")
parser.add_argument('--mode', default='per_student',
                    help="The grading mode, supports either 'per_problem' or 'per_student' grading")
parser.add_argument('--student_ids', type=str, help="path to the csv file that contains students names, emails.")
parser.add_argument('--nr_problems', type=int, default=None,
                    help="The number of problems to be checked, \
                     if None, then the number of problems will be determined automatically from one of the files.")
parser.add_argument('--with_assertions', action='store_true',
                    help="If True, then each problem should have assertion blocks (public and private) and \
                     the grading will be based on the outcomes of the assertions.")
parser.add_argument('--save_comments', action='store_true',
                    help="If True, then there will be comment recommendation based on previous comments.")
parser.add_argument('--detect_plagiarism', action='store_true',
                    help="If True, then the codes will be analyzed for potential plagiarism.")
parser.add_argument('--problems_to_check', nargs='+', default=None, type=int,
                    help="problems to check for plagiarism.")
parser.add_argument('--plagiarism_tol_level', type=float, default=None,
                    help="Float between 0 and 1 for the plagiarism tolerance level.")
parser.add_argument('--save_dendrograms', action='store_true',
                    help="If True, then the dendrogram plot of cheating clusters will be saved.")
parser.add_argument('--save_dir', type=str, default='graded',
                    help="folder name for the graded notebooks and generated plots to be saved in.")

args = parser.parse_args()

if __name__ == "__main__":
    # TODO: write a config parser instead of this if/else's
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

        sys.path.append(path)
        try:
            from assertions import hidden_assertions
        except ModuleNotFoundError:
            hidden_assertions = None
        with_assertions = args.with_assertions
        assertion_parser = AssertionParser(hidden_assertions=hidden_assertions)
    else:
        with_assertions = cf.with_assertions
        hidden_assertions = None
        assertion_parser = None

    save_dir = args.save_dir

    if args.detect_plagiarism:
        plagiarism_detector = PlagiarismDetector(save_dir=save_dir,
                                                 tol_level=args.plagiarism_tol_level,
                                                 save_dendrograms=args.save_dendrograms,
                                                 problems_to_check=args.problems_to_check,
                                                 add_one_cell=with_assertions)
    else:
        plagiarism_detector = None

    grader = Grader(path=path,
                    student_ids=args.student_ids,
                    mode=mode,
                    nr_problems=nr_problems,
                    with_assertions=with_assertions,
                    points=cf.points,
                    assertion_parser=assertion_parser,
                    plagiarism_detector=plagiarism_detector,
                    save_comments=args.save_comments,
                    save_dir=save_dir,
                    streamlit=False)
    grader.grade()
