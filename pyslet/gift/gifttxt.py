#! /usr/bin/env python
"""This module implements the GIFT specification defined by Moodle """

import giftns
import core
# import variables


class GIFTDocument(giftns.GIFTNSDocument):
	"""
	Same structure as qtixml.QTIDocument
	https://github.com/swl10/pyslet/blob/master/pyslet/qtiv2/xml.py#L23

	Used to represent all documents representing information from the
	GIFT specification (https://docs.moodle.org/23/en/GIFT_format).

	Simple recipe to get started::

		import pyslet.gift.gifttxt as gifttxt

		doc = gifttxt.GIFTDocument()
		with open('mygift.txt', 'rb') as f:
			doc.read(src=f)
			# do stuff with the GIFT document here

	The root (doc.root) element of a GIFT document may be one of a number
	of elements.  Look to implement an element like qtiv2.items.AssessmentItem
	https://github.com/swl10/pyslet/blob/master/pyslet/qtiv2/items.py#L15

	"""

	classMap = {}

	def __init__(self, **args):
		giftns.GIFTNSDocument.__init__(self, defaultNS=core.GIFT_NAMESPACE, **args)
		if isinstance(self.root, core.GIFTElement):
			self.root.set_attribute((giftns.NO_NAMESPACE, ".ns"), None)

	def get_element_class(self, name):
		return GIFTDocument.classMap.get(name, GIFTDocument.classMap.get(name[0], None), giftns.GIFTNSElement)

	def add_to_content_package(self):
		pass

# giftns.map_class_elements(GIFTDocument.classMap, globals())
# giftns.map_class_elements(GIFTDocument.classMap, variables)
# giftns.map_class_elements(GIFTDocument.classMap, content)
# giftns.map_class_elements(GIFTDocument.classMap, interactions)
# giftns.map_class_elements(GIFTDocument.classMap, items)
# giftns.map_class_elements(GIFTDocument.classMap, expressions)
