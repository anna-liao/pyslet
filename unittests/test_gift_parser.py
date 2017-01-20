#! /usr/bin/env python
import logging
import os.path
import unittest

import pyslet.rfc2396 as uri

from pyslet.gift import parser
from pyslet.gift import structures


def suite():
	return unittest.TestSuite((
		unittest.makeSuite(GIFTValidationTests, 'test')
	))


TEST_DATA_DIR = os.path.join(
	os.path.split(os.path.abspath(__file__))[0], 'data_gift')


class GIFTValidationTests(unittest.TestCase):

	def test_well_formed(self):
		dpath = os.path.join(TEST_DATA_DIR, 'wellformed')
		for fname in os.listdir(dpath):
			if fname[-4:] != ".txt":
				continue
			f = uri.URI.from_path(os.path.join(dpath, fname))
			with structures.GIFTEntity(f) as e:
				d = structures.Document()
				p = parser.GIFTParser(e)
				p.check_validity = False
				try:
					p.parse_document(d)
					self.assertTrue(
						p.valid is None,
						"Well-Formed Example: %s marked valid but "
						"check_validity was False" % fname)
				except parser.GIFTWellFormedError as e:
					self.fail("Well-Formed Example: %s raised "
						"GIFTWellFormedError\n%s" % (fname, str(e)))
		dpath = os.path.join(TEST_DATA_DIR, 'notwellformed')
		for fname in os.listdir(dpath):
			if fname[-4:] != ".txt":
				continue
			f = uri.URI.from_path(os.path.join(dpath, fname))
			with structures.GIFTEntity(f) as e:
				d = structures.Document()
				try:
					d.read(e)
					self.fail("%s is not Well-Formed but failed to raise "
						"GIFTWellFormedError" % fname)
				except parser.GIFTWellFormedError as e:
					logging.info("\n%s: Well-formed Errors:", fname)
					logging.info(str(e))
