#! /usr/bin/env python
import logging
import os.path
import unittest

import pyslet.rfc2396 as uri

from pyslet.gift import parser
from pyslet.gift import structures


def suite():
	return unittest.TestSuite((
		# unittest.makeSuite(GIFTValidationTests, 'test'),
		unittest.makeSuite(GIFTParserTests, 'test')
	))


TEST_DATA_DIR = os.path.join(
	os.path.split(os.path.abspath(__file__))[0], 'data_gift')


class GIFTValidationTests(unittest.TestCase):

	# def test_well_formed(self):
	# 	dpath = os.path.join(TEST_DATA_DIR, 'wellformed')
	def test_comment(self):
		dpath = os.path.join(TEST_DATA_DIR, 'comment')
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
		# dpath = os.path.join(TEST_DATA_DIR, 'notwellformed')
		# for fname in os.listdir(dpath):
		# 	if fname[-4:] != ".txt":
		# 		continue
		# 	f = uri.URI.from_path(os.path.join(dpath, fname))
		# 	with structures.GIFTEntity(f) as e:
		# 		d = structures.Document()
		# 		try:
		# 			d.read(e)
		# 			self.fail("%s is not Well-Formed but failed to raise "
		# 				"GIFTWellFormedError" % fname)
		# 		except parser.GIFTWellFormedError as e:
		# 			logging.info("\n%s: Well-formed Errors:", fname)
		# 			logging.info(str(e))


class GIFTParserTests(unittest.TestCase):

	def test_constructor(self):
		with structures.GIFTEntity("hello") as e:
			parser.GIFTParser(e)

	# def test_rewind(self):
	# 	data = "Hello\r\nWorld\nCiao\rTutti!"
	# 	data2 = "Hello\nWorld\nCiao\nTutti!"
	# 	with structures.GIFTEntity(data) as e:
	# 		p = parser.GIFTParser(e)
	# 		for i in range(len(data2)):
	# 			self.assertTrue(p.the_char == data2[i],
	# 				"Failed at data[%i] before look ahead" % i)
	# 			for j in range(5):
	# 				data = []
	# 				for k in range(j):
	# 					if p.the_char is not None:
	# 						data.append(p.the_char)
	# 					p.next_char()
	# 				p.buff_text(''.join(data))
	# 				self.assertTrue(p.the_char == data2[i],
	# 					"Failed at data[%i] after Rewind(%i)" % (i, j))
	# 			p.next_char()

	# def test_document(self):
	# 	os.chdir(TEST_DATA_DIR)
	# 	f = open('readFile.txt', 'rb')
	# 	with structures.GIFTEntity(f) as e:
	# 		d = structures.Document()
	# 		d.read(e)
	# 		root = d.root
	# 		self.assertTrue(isinstance(root, structures.Element))
	# 		self.assertTrue(root.get_value() == 'Hello World')
	# 	f.close()

	def test_comment(self):
		with structures.GIFTEntity("//Hello World") as e:
			p = parser.GIFTParser(e)
			pstr = p.parse_comment()
			self.assertTrue(pstr == "Hello World", "Match failed: %s (expected %s)" % (pstr, "Hello World"))
			# try:
			# 	if p.parse_literal('//'):
			# 		pstr = p.parse_comment()
			# 	self.fail("Parsed bad comment: %s" % pstr)
			# except parser.GIFTFatalError:
			# 	pass
