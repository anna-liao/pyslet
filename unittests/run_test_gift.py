#! /usr/bin/env python
"""Runs unit tests on gift modules only"""

import unittest
import logging

all_tests = unittest.TestSuite()
import test_gift_structures
all_tests.addTest(test_gift_structures.suite())
# import test_gift_namespace
# all_tests.addTest(test_gift_namespace.suite())


def suite():
	global all_tests
	return all_tests


def load_tests(loader, tests, pattern):
	return suite()


if __name__ == "__main__":
	# runner = unittest.TextTestRunner()
	# runner.run(suite())
	logging.basicConfig(level=logging.ERROR)
	unittest.main()
