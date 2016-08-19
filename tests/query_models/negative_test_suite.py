import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from query_test_suite import QueryTestSuite


class NegativeTestSuite(QueryTestSuite):
    """
      Represents a positive test case expectation.
      Used in the elasticsearch abstract class unit tests.
    """
    positive_test = False
