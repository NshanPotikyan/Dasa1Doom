from configs import general as cf


class AssertionParser:

    def __init__(self, hidden_assertions):
        self.hidden_assertions = hidden_assertions if hidden_assertions is not None else {}
        self.assertions_for_comments = None
        self.nr_assertions = None
        self.test_assertions = ''

    def __call__(self, problem_id, code_cell):
        only_code = code_cell.strip()

        assertions = self.hidden_assertions.get(problem_id, "")

        if 'return' not in only_code:
            # in case the exercise is not completed e.g.
            # the function has no return statement
            only_code = ""

        only_code = f'{cf.dependencies}\n{only_code}'
        # print(only_code, end='\n')
        # print(assertions)
        self._process_assertions(assertions)
        grade_str = f"grade = sum(test_assertions)/{self.nr_assertions}"
        failed = f"failed_assertions = [{self.assertions_for_comments}[i] for i, test in enumerate(test_assertions) if test == False]"
        final_code = f"{only_code}\n{self.test_assertions}\n{grade_str}\n{failed}"
        try:
            exec(final_code, globals())
        except Exception as e:
            print(e)
            # return 0, cf.all_incorrect
        comment = self._conditions2comment(failed_assertions, assertions)
        return grade, comment

    def _process_assertions(self, assertions):
        """
        Gets the number of assertions and the assertions for comments.
        """
        self.nr_assertions = assertions.count('assert')
        self.assertions_for_comments = []
        self.test_assertions = f"test_assertions = []\n"
        # TODO: go over this part
        for i in assertions.split('assert'):
            if not i:
                continue
            if ' = ' in i or i.startswith('#'):
                if ' ==' in i:
                    # in case the assertion line is here
                    for j in i.split('\n\n'):
                        if ' ==' in j:
                            self.assertions_for_comments.append(j.strip())
                            self.test_assertions += f"""try:
    test_assertions.append({j.strip()})
except:
    test_assertions.append(False)\n"""

                            # self.test_assertions += f'test_assertions.append({j.strip()})\n'
                        else:
                            self.test_assertions += f"{j}\n"
                else:
                    # in case of non-assertion line
                    self.test_assertions += f"{i}"
            else:
                self.assertions_for_comments.append(i.strip())
                self.test_assertions += f"""try:
    test_assertions.append({i.strip()})
except:
    test_assertions.append(False)\n"""

                # self.test_assertions += f'test_assertions.append({i.strip()})\n'

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
{failed_assertions}        
""".replace('[', '').replace(']', '').replace('"', '')


if __name__ == '__main__':
    from sample_homeworks.hw1.assertions import hidden_assertions
    sample_code = """def dist(a,b):
    if len(a) == len(b):
        return np.sqrt(sum((b-a)**2))
    else:
        return "DimensionError"
"""
    assertion_parser = AssertionParser(hidden_assertions=hidden_assertions)
    print(assertion_parser(code_cell=sample_code, problem_id=1))
