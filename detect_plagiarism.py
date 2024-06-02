import argparse

from utils.plagiarism_detector import PlagiarismDetectorStreamlit

parser = argparse.ArgumentParser(description="Homework checking.")

parser.add_argument('--path', default='sample_homeworks/with_assertions',
                    help="The path to the jupyter notebook files.")
parser.add_argument('--plagiarism_tol_level', type=float, default=0.9,
                    help="Float between 0 and 1 for the plagiarism tolerance level.")

args = parser.parse_args()

if __name__ == "__main__":
    plagiarism_detector = PlagiarismDetectorStreamlit(path=args.path,
                                                      tol_level=args.plagiarism_tol_level
                                                      )

    plagiarism_detector.detect()
