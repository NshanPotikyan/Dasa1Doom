import argparse

from utils.graders import GraderStreamlit

parser = argparse.ArgumentParser(description="Homework checking.")

parser.add_argument('--path', default='sample_homeworks/with_assertions',
                    help="The path to the jupyter notebook files.")

args = parser.parse_args()

if __name__ == "__main__":
    plagiarism_detector = GraderStreamlit(path=args.path)

    plagiarism_detector.grade()
