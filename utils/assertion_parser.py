import os

from configs import general as cf
from utils.misc import remove_difference


class AssertionParser:
    """
    :param dict or None hidden_assertions: assertions used for grading, keys are problem ids, values
        are tuples of (assertions, function_name) format
    """

    def __init__(self, hidden_assertions):
        self.hidden_assertions = hidden_assertions if hidden_assertions is not None else {}
        self.assertions_for_comments = None
        self.nr_assertions = None
        self.test_assertions = ''

    def import_dependencies(self):
        # run the dependencies globally (e.g. imports)
        dependencies = self.hidden_assertions.get(0, "")
        exec(dependencies, globals())

    def __call__(self, problem_id, code_cell):
        """
        :param int problem_id: problem index
        :param str code_cell: cell that contains the code
        :returns: grade and comment
        :rtype: tuple
        """
        only_code = code_cell.strip()

        assertions, func_name = self.hidden_assertions.get(problem_id, ["", ""])

        if 'return' not in only_code:
            # in case the exercise is not completed e.g.
            # the function has no return statement
            only_code = f"def {func_name}(*args, **kwargs): return -666"

        self._process_assertions(assertions)
        grade_str = f"grade = sum(test_assertions)/{self.nr_assertions}"
        failed = f"failed_assertions = [{self.assertions_for_comments}[i] for i, test in enumerate(test_assertions) if test == False]"
        final_code = f"{only_code}\n{self.test_assertions}\n{grade_str}\n{failed}"
        globals()['grade'] = None
        globals()['comment'] = None
        dict_before = globals()
        try:
            exec(final_code, globals())
            dict_after = globals()
        except Exception as e:
            return 0, f'{cf.all_incorrect} ({e})'

        # TODO: include assertions with Pass/Not Pass info
        comment = self._conditions2comment(failed_assertions, assertions)

        # remove newly defined names
        remove_difference(dict_before=dict_before, dict_after=dict_after)

        return grade, comment

    def _process_assertions(self, assertions):
        """
        Gets the number of assertions and the assertions for comments.
        """
        self.nr_assertions = assertions.count('assert')
        self.assertions_for_comments = []
        self.test_assertions = f"test_assertions = []\n"
        for i in assertions.split('assert'):

            if not i.strip():
                continue
            if ' = ' in i or i.startswith('#'):
                if ' ==' in i or ' !=' in i:
                    self._assertion2test(i)
                else:
                    # in case of non-assertion line
                    self.test_assertions += f"{i}"
            else:
                self._assertion2test(i)

    def _assertion2test(self, assertion):
        for j in assertion.split('\n\n'):

            if ' ==' in j or ' !=' in j:
                self.assertions_for_comments.append(j.strip())
                self.test_assertions += f"""try:
    test_assertions.append({j.strip()})
except:
    test_assertions.append(False)\n"""
            else:
                self.test_assertions += f"{j}\n"

    @staticmethod
    def _conditions2comment(failed_assertions, assertions):
        """
        Transforms the list of conditions into a comment/feedback
        :param failed_assertions: list of str containing the assertion conditions
        :param assertions: list of str for all assertions
        :return: str of the comment
        """
        if len(failed_assertions) == len(assertions):
            return cf.all_incorrect
        elif len(failed_assertions) == 0:
            return cf.default_comment
        else:
            return f"""{cf.assertion_comment}
{str(failed_assertions)[1:-1]}        
""".replace('"', '')


if __name__ == '__main__':
    from sample_homeworks.with_assertions.assertions import hidden_assertions

    sample_code1 = """
    """
    assertion_parser = AssertionParser(hidden_assertions=hidden_assertions)
    print(assertion_parser(code_cell=sample_code1, problem_id=2))
