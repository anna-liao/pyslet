#! /usr/bin/env python
# import sys
# sys.path.append('..')
import unittest
from pyslet.gift import structures


def suite():
	return unittest.TestSuite((
		# unittest.makeSuite(GIFTCharacterTests, 'test'),
		unittest.makeSuite(GIFTEntityTests, 'test'),
		unittest.makeSuite(ElementTests, 'test')
		# unittest.makeSuite(DocumentTests, 'test')
	))


# class GIFTCharacterTests(unittest.TestCase):

# 	def test_space(self):
# 		"""[3] S ::= (#x20 | #x9 | #xD | #xA)+"""
# 		expected_edges = [0x9, 0xB, 0xD, 0xE, 0x20, 0x21]
# 		self.assertTrue(self.find_edges(structures.is_s, 256) ==
# 			expected_edges, "is_s")

# 	def find_edges(self, test_func, max):
# 		edges = []
# 		flag = False
# 		for code in range(max + 1):
# 			if flag != test_func(str(code)):
# 				flag = not flag
# 				edges.append(code)
# 		if flag:
# 			edges.append(max + 1)
# 		return edges

def decode_yn(value):
	return value == 'Yes'


def encode_yn(value):
	if value:
		return 'Yes'
	else:
		return 'No'


class GenericElementA(structures.Element):
	pass


class GenericSubclassA(GenericElementA):
	pass


class GenericElementB(structures.Element):
	pass


class GenericSubclassB(GenericElementB):
	pass


class ReflectiveElement(structures.Element):
	GIFTNAME = "reflection"

	GIFTATTR_btest = 'bTest'
	GIFTATTR_ctest = ('cTest', decode_yn, encode_yn)
	GIFTATTR_dtest = ('dTest', decode_yn, encode_yn, list)
	GIFTATTR_dtestR = ('dTestR', decode_yn, encode_yn)  # legacy test
	GIFTATTR_etest = ('eTest', decode_yn, encode_yn, dict)
	GIFTATTR_etestR = ('eTestR', decode_yn, encode_yn) 	# legacy test
	GIFTATTR_ftest = 'fTest'		# missing attribute value

	def __init__(self, parent):
		structures.Element.__init__(self, parent)
		self.atest = None
		self.bTest = None
		self.cTest = None
		self.dTest = None
		self.dTestR = []
		self.eTest = None
		self.eTestR = {}
		self.child = None
		self.generics = []
		self.GenericElementB = None

	def get_children(self):
		for child in structures.Element.get_children(self):
			yield child
		if self.child:
			yield self.child

	def ReflectiveElement(self):    # noqa
		if self.child:
			return self.child
		else:
			e = ReflectiveElement(self)
			self.child = e
			return e

	def GenericElementA(self, childClass=GenericElementA):  # noqa
		child = childClass(self)
		self.generics.append(child)
		return child


class ReflectiveDocument(structures.Document):

	@classmethod
	def get_element_class(cls, name):
		if name in ["reflection", "etest"]:
			return ReflectiveElement
		else:
			return structures.Element


class GIFTEntityTests(unittest.TestCase):

	def test_constructor(self):
		e = structures.GIFTEntity(b"hello")
		self.assertTrue(e.line_num == 1)
		self.assertTrue(e.line_pos == 1)

	def test_chars(self):
		e = structures.GIFTEntity(b"hello")
		for c in "hello":
			self.assertTrue(e.the_char == c)
			e.next_char()
		self.assertTrue(e.the_char is None)

	def test_lines(self):
		e = structures.GIFTEntity(b"Hello\nWorld\n!")
		while e.the_char is not None:
			e.next_char()
		self.assertTrue(e.line_num == 3)
		self.assertTrue(e.line_pos == 2)


class NamedElement(structures.Element):
	GIFTNAME = "test"
	GIFTCONTENT = structures.ElementType.ElementContent


class ElementTests(unittest.TestCase):

	def test_constructor(self):
		e = structures.Element(None)
		self.assertTrue(e.giftname is None, 'element name on construction')
		self.assertTrue(e.get_document() is None, 'document set on construction')
		attrs = e.get_attributes()
		self.assertTrue(len(list(dict.keys(attrs))) == 0,
			"Attributes present on construction")
		children = e.get_children()
		try:
			next(children)
			self.fail("Children present on construction")
		except StopIteration:
			pass

	def test_default_name(self):
		e = NamedElement(None)
		self.assertTrue(
			e.giftname == 'test', 'element default name on construction')

	def test_set_gift_name(self):
		e = NamedElement(None)
		e.set_giftname('test2')
		self.assertTrue(e.giftname == 'test2',
			'element named explicitly in construction')

	def test_attributes(self):
		e = structures.Element(None)
		e.set_giftname('test')
		e.set_attribute('atest', 'value')
		attrs = e.get_attributes()
		self.assertTrue(len(list(dict.keys(attrs))) == 1, "Attribute not set")
		self.assertTrue(attrs['atest'] == 'value', "Attribute not set correctly")
		e = ReflectiveElement(None)
		e.set_attribute('atest', 'value')
		attrs = e.get_attributes()
		self.assertTrue(attrs['atest'] == 'value', "Attribute not set correctly")
		e.set_attribute('btest', 'Yes')
		self.assertTrue(e.bTest == 'Yes', "Attribute reflection with simple assignment")
		attrs = e.get_attributes()
		self.assertTrue(attrs['btest'] == 'Yes', "Attribute not set correctly")
		e.set_attribute('ctest', 'Yes')
		self.assertTrue(e.cTest is True, "Attribute reflection with decode/encode")
		attrs = e.get_attributes()
		self.assertTrue(attrs['ctest'] == 'Yes', "Attribute not set correctly")
		self.assertFalse('dtest' in attrs, "Optional ordered list attribute")
		self.assertTrue(attrs['dtestR'] == '', "Required ordered list attribute")
		e.set_attribute('dtest', 'Yes No')
		self.assertTrue(e.dTest == [True, False],
			"Attribute reflection with list; %s" % repr(e.dTest))
		attrs = e.get_attributes()
		self.assertTrue(attrs['dtest'] == 'Yes No', "Attribute not set correctly")
		self.assertFalse('etest' in attrs, "Optional unordered list attribute")
		self.assertTrue(attrs['etestR'] == '', "Required unordered list attribute")
		e.set_attribute('etest', 'Yes No Yes')
		self.assertTrue(e.eTest == {True: 2, False: 1}, "Attribute reflection with list: %s" % repr(e.eTest))
		attrs = e.get_attributes()
		self.assertTrue(attrs['etest'] == 'No Yes Yes', "Attribute not set correctly: %s" % repr(attrs['etest']))
