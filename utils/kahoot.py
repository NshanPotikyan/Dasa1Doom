import pandas as pd

import utils.misc as um


class KahootParser:
    """
    :param str path_to_folder: should contain xlsx files of Kahoot reports
    :param dict or str student_ids: either the final dict is provided, or path to the csv file
        that contains 0 (Ids), 1 (Names)
    """

    def __init__(self, path_to_folder, student_ids):
        self.student_ids = um.get_student_info(student_ids)
        self.files = um.get_files(path=path_to_folder, file_type='xlsx')
        self.correct_name_mapping = {}

    def parse_one_kahoot(self, one_kahoot):
        """
        Parses one kahoot report by leaving relevant information and assigns names to students.

        :param str one_kahoot: path to xlsx file
        :returns:
        :rtype: pandas.DataFrame
        """
        data = pd.read_excel(one_kahoot, sheet_name="RawReportData Data")
        data = data[["Question Number", "Player", "Correct", "Answer Time (seconds)"]]
        data.rename(columns={
            'Question Number': 'question_id',
            'Player': 'student',
            'Correct': 'correct',
            'Answer Time (seconds)': 'time'
        }, inplace=True)
        data.question_id = data.question_id.str.replace(' Quiz', '').astype(int)

        for k in data.student.unique():
            if k in self.correct_name_mapping:
                continue

            candidate_name = um.find_in_dict(some_dict=self.student_ids,
                                             key=um.keep_letters(k))
            if len(candidate_name) == 1:
                self.correct_name_mapping[k] = candidate_name[0]
            else:
                self.correct_name_mapping[k] = input(f'Enter the id for {k}')
        data['student_id'] = data.student.map(self.correct_name_mapping)
        return data

    def parse_one_csv(self, one_csv):
        """
        Parses one processed kahoot report and assigns ids to students.

        :param str one_csv: path to csv file
        :returns:
        :rtype: pandas.DataFrame
        """
        data = pd.read_csv(one_csv)
        data = data[['question_id', 'student_id', 'correct', 'time']]
        data.student_id = data.student_id.map(self.student_ids)
        return data

    def process_kahoot_xlsxs(self):
        """
        Goes over all kahoot reports and generates csv files by leaving relevant information.
        """
        for file in self.files:
            self.parse_one_kahoot(file).to_csv(file.replace('xlsx', 'csv'), index=False)

    def replace_names_with_ids(self):
        """
        Goes over all processed kahoot reports and generates csv files without student names in them.
        """
        for file in self.files:
            csv_name = file.replace('xlsx', 'csv')
            self.parse_one_csv(csv_name).to_csv(csv_name.replace(' ', ''), index=False)


if __name__ == '__main__':
    kahoot_parser = KahootParser(path_to_folder='kahoots',
                                 student_ids='students.csv')
    kahoot_parser.replace_names_with_ids()
