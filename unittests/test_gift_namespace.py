#! /usr/bin/env python

import io
import unittest

from pyslet.gift.structures import ElementType
import pyslet.gift.giftns as giftns


def suite():
	return unittest.TestSuite((
		unittest.makeSuite(GIFTNSElementTests, 'test')
		))

# Basic comment
EXAMPLE_1 = b"""//Hello World"""


class GIFTNSValidationTests(unittest.TestCase):
	def test_name(self):
		"""Checks for valid NCName, non-colonized Name.
		This is a XML datatype, so unclear whether it is
		needed for GIFT namespaces.
		https://www.w3.org/TR/1999/WD-xmlschema-2-19990924/#NCName
		"""
		pass


class GIFTNSElementTests(unittest.TestCase):
	def test_constructor(self):
		e = giftns.NSElement(None)
		self.assertTrue(e.ns is None, 'ns set on construction')
		self.assertTrue(e.giftname is None,
			               'element name not set on construction')
