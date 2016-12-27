#! /usr/bin/env python

from . import core

class BooleanValue:

	"""Represents single values of type :py:class:`BaseType.boolean`."""
	def __init__(self, value=None):
		if value is not None:
			self.set_value(value)

	def set_value(self, value):
		pass

class Container:
	pass

class MultipleContainer(Container):
	"""
	usage:
	in test_gift.VariableTests.test_mapping
		value = variables.MultipleContainer(mapping.baseType)
		value.set_value(iter(v))
	"""
		 
