#! /usr/bin/env python

import unittest
from ..pyslet.gift import structures


def suite():
	return unittest.TestSuite((
		unittest.makeSuite(GIFTEntityTests, 'test')
		# unittest.makeSuite(ElementTests, 'test'),
		# unittest.makeSuite(DocumentTests, 'test')
	))


class GIFTEntityTests(unittest.TestCase):

	def test_chars(self):
		e = structures.GIFTEntity(b"hello")
		for c in "hello":
			self.assertTrue(e.the_char == c)
			e.next_char()
		self.assertTrue(e.the_char is None)
