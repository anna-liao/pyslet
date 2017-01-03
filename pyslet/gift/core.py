#! /usr/bin/env python

# import structures as gift
import giftns

GIFT_NAMESPACE = "Moodle GIFT"
"""IMSQTI_NAMESPACE = "http://www.imsglobal.org/xsd/imsqti_v2p1"
The namespace used to recognise elements in XML documents."""


class GIFTError(Exception):
	"""Abstract class used for all GIFT exceptions."""
	pass


class ProcessingError(GIFTError):
	"""Error raised when an invalid processing element is encountered."""
	pass


class GIFTValidityError(GIFTError):
	pass


def validate_identifier(value, prefix='_'):
	"""Decodes an identifier from a string.

	https://github.com/swl10/pyslet/blob/master/pyslet/qtiv2/core.py#L61
	"""
	pass


class GIFTElement(giftns.GIFTNSElement):
	"""Basic element to represent all GIFT elements

	Syntax for python classes: https://docs.python.org/3/tutorial/classes.html
	"""
	pass


class DeclarationContainer():
	"""An abstract mix-in class used to manage a dictionary of variable declarations."""
	pass
