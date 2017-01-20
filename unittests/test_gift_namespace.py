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


class GIFTExampleElement(giftns.NSElement):
	GIFTCONTENT = ElementType.ElementContent


class GIFTExampleDocument(giftns.NSDocument):
	default_ns = "http://www.example.com"

	@classmethod
	def get_element_class(cls, name):
		if name[1] in ("createTag"):
			return GIFTExampleElement
		else:
			return giftns.NSDocument.get_element_class(name)


class GIFTNSDocumentTests(unittest.TestCase):

	def test_read_string(self):
		"""Test the reading of the NSDocument from a supplied stream"""
		d = giftns.NSDocument()
		d.read(src=io.BytesIO(EXAMPLE_1))
		root = d.root
		self.assertTrue(isinstance(root, giftns.NSElement))
		self.assertTrue(root.ns is None and root.giftname == '' and root.get_value() == 'Hello World')
