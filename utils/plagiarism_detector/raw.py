import os
import numpy as np
import matplotlib.pyplot as plt

from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

from configs import general as cf
from utils.code_similarity import detect, summarize
import utils.notebook as un


class PlagiarismDetector:
    """
    :param str save_dir: defines the directory where the generated files (notebooks, plots) will be saved
    :param list[int] problems_to_check: defines which problems we want to check for plagiarism
    :param float tol_level: the sensitivity/confidence of the detection
    :param bool save_dendrograms: specifies whether we want to save the dendrogram plots
    :param bool add_one_cell: specifies whether we want to add the grade after 3 or 2 cells wrt the problem statement
    """
    def __init__(self, save_dir,
                 problems_to_check=range(1, 11),
                 tol_level=cf.plagiarism_tol_level,
                 save_dendrograms=False,
                 add_one_cell=False):
        self.save_dir = save_dir
        self.problems_to_check = problems_to_check
        self.tol_level = tol_level
        self.save_dendrograms = save_dendrograms
        self.add_one_cell = add_one_cell

    def __call__(self, files, students):
        """
        Goes over all the problems for each student
        searches for potential plagiarism, asks the user to double check the detection
        and penalizes if needed
        :return:
        """
        names = None
        similarity_tensor = []
        for i in self.problems_to_check:
            codes = []
            names = []

            for j, student in enumerate(students):
                _, _, cells, idx = un.find_cell_id_per_notebook(files=files,
                                                                file_name=student,
                                                                some_text=f'{cf.problem_starts_with}{i}')

                if idx is None:
                    continue

                codes.append(cells[idx + 1])
                names.append(student)

            cheaters, similarity_matrix = self.detect_summarize(codes, names,
                                                                tolerance_level=self.tol_level)
            diss_matrix = 1 - similarity_matrix

            if self.save_dendrograms:
                self.plot_dendrogram(matrix=diss_matrix,
                                     labels=names,
                                     title=f'Problem{i}',
                                     save_dir=self.save_dir)

            similarity_tensor.append(diss_matrix)

            for students in cheaters:
                files = self.penalize(files=files,
                                      student_names=students,
                                      problem_id=f'{cf.problem_starts_with}{i}')

        if self.save_dendrograms and names is not None:
            similarity_tensor = np.array(similarity_tensor)
            mean_similarity = similarity_tensor.mean(axis=0)
            self.plot_dendrogram(mean_similarity,
                                 labels=names,
                                 title='OverAllProblems',
                                 save_dir=self.save_dir)

    def penalize(self, files, student_names, problem_id):
        """
        Set the grade and comment of those students who have cheated
        :param list[str] files: notebook file paths
        :param list[str] student_names: list of strings for student names
        :param str problem_id: problem identifier
        :return:
        """
        for student_name in student_names:
            hw, notebook, cells, idx = un.find_cell_id_per_notebook(files=files,
                                                                    file_name=student_name,
                                                                    some_text=problem_id)

            notebook = un.insert_cell(notebook,
                                      position=idx + 2 + self.add_one_cell,
                                      content=0,
                                      content_type='grade')
            notebook = un.insert_cell(notebook,
                                      position=idx + 3 + self.add_one_cell,
                                      content=cf.plagiarism_comment,
                                      content_type='comment')

            files = un.save_notebook(file_dict=notebook,
                                     file_name=hw,
                                     update=True,
                                     files=files,
                                     save_dir=self.save_dir)
        return files

    @staticmethod
    def detect_summarize(pycode_list, names, tolerance_level=0.9):
        """
        Goes over all code strings and looks for potential plagiarism
        :param pycode_list: list of str containing python code
        :param names: list of str containing student names
        :param tolerance_level: float of the plagiarism tolerance level
        :return:
        """
        nr_codes = len(pycode_list)
        similarity_matrix = np.ones((nr_codes, nr_codes))
        cheaters = []
        for i in range(nr_codes):
            try:
                results = detect(pycode_list[i:], keep_prints=True, module_level=True)
            except SyntaxError:
                continue
            for index, func_ast_diff_list in results:
                sum_plagiarism_percent, _, _ = summarize(func_ast_diff_list)
                similarity_matrix[i, index + i] = round(sum_plagiarism_percent, 2)
                if sum_plagiarism_percent > tolerance_level:
                    # print('{:.2f} % of {} code structure is similar with {} code structure.'.format(
                    #     sum_plagiarism_percent * 100, names[i], names[index + i]))
                    print(pycode_list[i])
                    print(pycode_list[i + index])
                    penalize = input('Do you want to penalize for plagiarism? Yes(1) or '
                                     'press Enter without entering anything')
                    if penalize:
                        cheaters.append([names[i], names[i + index]])

        # make the similarity matrix symmetric
        i_lower = np.tril_indices(nr_codes, -1)
        similarity_matrix[i_lower] = similarity_matrix.T[i_lower]
        return cheaters, similarity_matrix

    @staticmethod
    def plot_dendrogram(matrix, labels=None, title='', color_threshold=0.3, linkage_type='single', save_dir=''):
        """
        Plot the dendrogram of the clustering
        :param matrix: numpy array of similarity matrix
        :param labels: list of str for leaf names
        :param title: str of the plot title
        :param color_threshold: float for coloring the tree linkages as clusters, below the specified value
        :param linkage_type: str type of linkage to apply (see sklearn documentation for more info)
        :param str save_dir: directory to save the figure in
        :return:
        """
        if labels is None:
            labels = [f'{i}' for i in np.arange(len(matrix))]
        dists = squareform(matrix)
        linkage_matrix = linkage(dists, linkage_type)
        plt.figure(figsize=(15, 10))
        dendrogram(linkage_matrix, color_threshold=color_threshold,
                   labels=labels, show_contracted=True, leaf_rotation=90)
        plt.ylabel('Dissimilarity')
        plt.title(f'{title}')
        plt.savefig(os.path.join(save_dir, f'{title}.jpg'))
