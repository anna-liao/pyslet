#! /usr/bin/env python
import sys
sys.path.append('..')
import unittest
from pyslet.gift import structures


def suite():
	return unittest.TestSuite((
		unittest.makeSuite(GIFTCharacterTests, 'test'),
		unittest.makeSuite(GIFTEntityTests, 'test')
		# unittest.makeSuite(ElementTests, 'test'),
		# unittest.makeSuite(DocumentTests, 'test')
	))


class GIFTCharacterTests(unittest.TestCase):

	def test_space(self):
		"""[3] S ::= (#x20 | #x9 | #xD | #xA)+"""
		expected_edges = [0x9, 0xB, 0xD, 0xE, 0x20, 0x21]
		self.assertTrue(self.find_edges(structures.is_s, 256) ==
			expected_edges, "is_s")


class GIFTEntityTests(unittest.TestCase):

	def test_chars(self):
		e = structures.GIFTEntity(b"hello")
		for c in "hello":
			self.assertTrue(e.the_char == c)
			e.next_char()
		self.assertTrue(e.the_char is None)
