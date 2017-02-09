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

	def test_well_formed(self):
		# dpath = os.path.join(TEST_DATA_DIR, 'wellformed')
		pass

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


class GIFTParserTests(unittest.TestCase):

	def test_constructor(self):
		with structures.GIFTEntity("hello") as e:
			parser.GIFTParser(e)

	def test_rewind(self):
		data = "Hello\r\nWorld\nCiao\rTutti!"
		data2 = "Hello\nWorld\nCiao\nTutti!"
		with structures.GIFTEntity(data) as e:
			p = parser.GIFTParser(e)
			for i in range(len(data2)):
				self.assertTrue(p.the_char == data2[i],
					"Failed at data[%i] before look ahead" % i)
				for j in range(5):
					data = []
					for k in range(j):
						if p.the_char is not None:
							data.append(p.the_char)
						p.next_char()
					p.buff_text(''.join(data))
					self.assertTrue(p.the_char == data2[i],
						"Failed at data[%i] after Rewind(%i)" % (i, j))
				p.next_char()

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

	def test_s(self):
		with structures.GIFTEntity(" \t\r\n \r \nH ello") as e:
			p = parser.GIFTParser(e)
			self.assertTrue(p.parse_s() == " \t\n \n \n")
			self.assertTrue(p.the_char == 'H')
			p.next_char()
			try:
				p.parse_required_s()
			except parser.GIFTWellFormedError:
				self.fail("parse_required_s failed to parse white space")
			try:
				p.parse_required_s()
				self.fail("parse_required_s failed to throw exception")
			except parser.GIFTWellFormedError:
				pass

	def test_name(self):
		# tests for escape chars.  one name in each string.
		# unittest for parser.parse_name()
		pass

	def test_names(self):
		# test for escape chars.  multiple names in one string.
		# unittest for parser.parse_names()
		pass

	def test_nmtoken(self):
		# test for escape chars.  one token in each string.
		# unittest for parser.parse_nmtoken()
		pass

	def test_nmtokens(self):
		# multiple tokens in one string.
		# unittest for parser.parse_nmtokens()
		pass

	def test_entity_value(self):
		# Test for XML references, where quotes are special escape characters
		# Not relevant for GIFT
		pass

	def test_char_data(self):
		with structures.GIFTEntity("First\nSecond\nThird\nFourth\n") as e:
			m = ['First', 'Second', 'Third', 'Fourth']
			p = parser.GIFTParser(e)
			p.doc = structures.Document()
			for match in m:
				p.element = structures.Element(p.doc)
				p.parse_char_data()
				p.next_char()
				self.assertTrue(p.element.get_value() == match,
					"Match failed: %s (expected %s)" % (p.element.get_value(), match))

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

	def test_misc(self):
		s = "//comment"
		with structures.GIFTEntity(s) as e:
			p = parser.GIFTParser(e)
			p.parse_misc()
			self.assertTrue(p.the_char is None, "Short parse of Misc")

	# def test_true_false(self):
	# 	s = """::Q1:: 1+1=2 {T}"""
	# 	with structures.GIFTEntity(s) as e:
	# 		p = parser.GIFTParser(e)
	# 		element = p.element = structures.Element("a")
	# 		p.parse_element()
	# 		children = list(element.get_children())

	def test_element(self):
		# s = """//comment\n"""
		# s = "::Question title\n"
		s = """//comment\n::Question title\n::Question{\n=A correct answer\n~Wrong answer1\n~Wrong answer2\n~Wrong answer3\n}"""
		with structures.GIFTEntity(s) as e:
			p = parser.GIFTParser(e)
			element = p.element = structures.Element("a")
			p.parse_element()
			children = list(element.get_children())
			self.assertTrue(len(children) == 6, "Number of children: %i" % len(children))
			self.assertTrue(isinstance(children[0], structures.Element), "First element: %s" % repr(children[0]))
			self.assertTrue(children[0].giftname == 'questionTitle', "First element name: %s" % repr(children[0].giftname))
			self.assertTrue(children[0].get_value() == 'Question title', "First element value: %s" % repr(children[0].get_value()))
			self.assertTrue(isinstance(children[1], structures.Element), "Second element: %s" % repr(children[1]))
			self.assertTrue(children[1].giftname == 'question', "Second element name: %s" % repr(children[1].giftname))
			self.assertTrue(children[1].get_value() == "Question", "Second element value: %s" % repr(children[1].get_value()))
			self.assertTrue(isinstance(children[2], structures.Element), "Third element: %s" % repr(children[2]))
			self.assertTrue(children[2].giftname == 'correctResponse', "Third element name: %s" % repr(children[2].giftname))
			self.assertTrue(children[2].get_value() == 'A correct answer', "Third element value: %s" % repr(children[3].get_value()))
			self.assertTrue(isinstance(children[3], structures.Element), "Fourth element: %s" % repr(children[3]))
			self.assertTrue(children[3].giftname == 'wrongResponse', "Fourth element name: %s" % repr(children[3].giftname))
			self.assertTrue(children[3].get_value() == "Wrong answer1", "Fourth element value: %s" % repr(children[3].get_value()))

			self.assertTrue(isinstance(children[4], structures.Element), "Fifth element: %s" % repr(children[4]))
			self.assertTrue(children[4].giftname == 'wrongResponse', "Fifth element name: %s" % repr(children[4].giftname))
			self.assertTrue(children[4].get_value() == "Wrong answer2", "Fifth element value: %s" % repr(children[5].get_value()))
			self.assertTrue(isinstance(children[5], structures.Element), "Sixth element: %s" % repr(children[5]))
			self.assertTrue(children[5].giftname == 'wrongResponse', "Sixth element name: %s" % repr(children[5].giftname))
			self.assertTrue(children[5].get_value() == "Wrong answer3", "Sixth element value: %s" % repr(children[5].get_value()))

	# def test_empty_question(self):
	# 	empty_q = ":: Question title :: Question {}"
	# 	p = parser.GIFTParser(e)
	# 	pstr = p.parse_comment()

if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	unittest.main()
