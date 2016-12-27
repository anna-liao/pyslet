#! /usr/bin/env python

"""
GIFT format examples taken from:
https://docs.moodle.org/23/en/GIFT_format

"""

import unittest

"""
def suite():
	return unittest.TestSuite((
		unittest.makeSuite(VariableTests, 'test'),
		#unittest.makeSuite(ExpressionTests, 'test')
	))
"""

import sys
sys.path.append('..')
import pyslet.gift.gifttxt as gifttxt

class VariableTests(unittest.TestCase):

	def test_mapping(self):
		"""
		Multiple choice with multiple right answers
		Based on: https://github.com/swl10/pyslet/blob/master/unittests/test_imsqtiv2p1.py#L507

		"""
		sample = b"""What two people are entombed in Grant's tomb? {
			~%-100%No one
			~%50%Grant
			~%50%Grant's wife
			~%-100%Grant's father
		}"""
		doc = gifttxt.GIFTDocument()
		doc.read(src=BytesIO(sample))
		# mapping.baseType is a Container
		mapping = doc.root.ResponseDeclaration[0].Mapping
		for v, mv in dict.items({
			("No one",): -1.0,
			("Grant",): 0.5,
			("Grant", "Grant's wife"): 1.0,
			("Grant's wife",): 0.5,
			("Grant's father",): -1.0,
			("",): 0.0}):

			value = variables.MultipleContainer(mapping.baseType)
			value.set_value(iter(v))
			mvalue = mapping.MapValue(value)
			self.assertTrue(isinstance(mvalue, variables.FloatValue),
							"MapValue response type")
			self.assertTrue(mvalue.value == mv,
							"Mapping failed for multiple %s, returned %.1f" %
							(v, mvalue.value))
			value = variables.OrderedContainer(mapping.baseType)
			value.set_value(iter(v))
			mvalue = mapping.MapValue(value)
			self.assertTrue(mvalue.value == mv,
							"Mapping failed for ordered %s, returned %.1f" %
							(v, mvalue.value))
			value = variables.OrderedContainer(mapping.baseType)
			value.set_value(iter(v))
			mvalue = mapping.MapValue(value)
			self.assertTrue(mvalue.value == mv,
							"Mapping failed for ordered %s, returned %.1f" %
							(v, mvalue.value))

class ExpressionTests(unittest.TestCase):

	def setUp(self):
		sample = b"""// question: 1 name: Grants tomb
			::Grants tomb::Who is buried in Grant's tomb in New York City? {
			=Grant
			~No one
			#Was true for 12 years, but Grant's remains were buried in the tomb in 1897
			~Napoleon
			#He was buried in France
			~Churchill
			#He was buried in England
			~Mother Teresa
			#She was buried in India
			}"""
		#self.doc = gifttxt.GIFTDocument()
		#self.doc.read(src=BytesIO(sample))

	def tearDown(self):
		pass

	def test_correct(self):
		pass

if __name__ == '__main__':
    unittest.main()
