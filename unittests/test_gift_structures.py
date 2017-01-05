#! /usr/bin/env python
# import sys
# sys.path.append('..')
import unittest
import os.path
import shutil
import logging

from tempfile import mkdtemp
from pyslet import rfc2396 as uri
from pyslet.gift import structures


def suite():
	return unittest.TestSuite((
		# unittest.makeSuite(GIFTCharacterTests, 'test'),
		unittest.makeSuite(GIFTEntityTests, 'test'),
		unittest.makeSuite(ElementTests, 'test'),
		unittest.makeSuite(DocumentTests, 'test')
	))

TEST_DATA_DIR = os.path.join(
	os.path.split(os.path.abspath(__file__))[0], 'data_gift')

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


class NamedElement(structures.Element):
	GIFTNAME = "test"
	GIFTCONTENT = structures.ElementType.ElementContent


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


class EmptyElement(structures.Element):
	GIFTNAME = "empty"
	GIFTCONTENT = structures.GIFTEmpty


class ElementContent(structures.Element):
	GIFTNAME = "elements"
	GIFTCONTENT = structures.ElementType.ElementContent


class MixedElement(structures.Element):
	GIFTNAME = "mixed"
	GIFTCONTENT = structures.ElementType.Mixed


class IDElement(structures.Element):
	GIFTName = "ide"
	GIFTCONTENT = structures.GIFTEmpty
	ID = "id"


class BadElement:
	GIFTNAME = "bad"


class Elements:
	named = NamedElement
	reflective = ReflectiveElement
	empty = EmptyElement
	elements = ElementContent
	mixed = MixedElement
	id = IDElement
	bad = BadElement


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
		try:
			if e.ztest:
				pass
			self.fail("AttributeError required for undefined names")
		except AttributeError:
			pass
		e.ztest = 1
		if e.ztest:
			pass
		del e.ztest
		try:
			if e.ztest:
				pass
			self.fail("AttributeError required for undefined names after del")
		except AttributeError:
			pass
		try:
			self.assertTrue(e.fTest is None, "Missing attribute auto value not None")
		except AttributeError:
			self.fail("Missing attribute auto value: AttributeError")
		e.fTest = 1
		del e.fTest
		try:
			self.assertTrue(
				e.fTest is None,
				"Missing attribute auto value not None (after del)")
		except AttributeError:
			self.fail(
				"Missing attribute auto value: AttributeError (after del)")

	def test_child_elements(self):
		"""Test child element behaviour"""
		e = structures.Element(None)
		e.set_giftname('test')
		e.add_child(structures.Element, 'test1')
		children = list(e.get_children())
		self.assertTrue(len(children) == 1, "add_child failed to add child element")

	def test_child_element_reflection(self):
		"""Test child element cases using reflection"""
		e = ReflectiveElement(None)
		child1 = e.add_child(ReflectiveElement, 'test1')
		self.assertTrue(e.child is child1, "Element not set by reflection")
		children = list(e.get_children())
		self.assertTrue(len(children) == 1 and children[0] is child1,
			"add_child failed to add child element")

		# Now create a second child, should return the same one due to model restriction
		child2 = e.add_child(ReflectiveElement, 'test1')
		self.assertTrue(e.child is child1 and child2 is child1, "Element model violated")
		child3 = e.add_child(GenericElementA, 'test3')
		self.assertTrue(e.generics[0] is child3, "Generic element")
		child4 = e.add_child(GenericSubclassA, 'test4')
		self.assertTrue(e.generics[1] is child4, "Generic sub-class element via method")
		child5 = e.add_child(GenericSubclassB, 'test5')
		self.assertTrue(e.GenericElementB is child5, "Generic sub-class element via member")

	def test_data(self):
		e = structures.Element(None)
		self.assertTrue(e.is_mixed(), "Mixed default")
		e.add_data('Hello')
		self.assertTrue(e.get_value() == 'Hello', "Data value")
		children = list(e.get_children())
		self.assertTrue(len(children) == 1, "Data child not set")
		self.assertTrue(children[0] == "Hello", "Data child not set correctly")

	def test_empty(self):
		e = EmptyElement(None)
		self.assertFalse(e.is_mixed(), "EmptyElement is mixed")
		self.assertTrue(e.is_empty(), "EmptyElement not empty")
		try:
			e.add_data('Hello')
			self.fail("Data in EmptyElement")
		except structures.GIFTValidityError:
			pass
		try:
			e.add_child(structures.Element)
			self.fail("Elements allows in EmptyElement")
		except structures.GIFTValidityError:
			pass

	def test_element_content(self):
		e = ElementContent(None)
		self.assertFalse(e.is_mixed(), "ElementContent appears mixed")
		self.assertFalse(e.is_empty(), "ElementContent appears empty")
		try:
			e.add_data('Hello')
			self.fail("Data in ElementContent")
		except structures.GIFTValidityError:
			pass
		# white space should silently be ignored.
		e.add_data('  \n\r  \t')
		children = list(e.get_children())
		self.assertTrue(len(children) == 0, "Unexpected children")
		# elements can be added
		e.add_child(structures.Element)
		children = list(e.get_children())
		self.assertTrue(len(children) == 1, "Expected one child")

	def test_mixed_content(self):
		e = MixedElement(None)
		self.assertTrue(e.is_mixed(), "MixedElement not mixed")
		self.assertFalse(e.is_empty(), "MixedElement appears empty")
		e.add_data('Hello')
		self.assertTrue(e.get_value() == 'Hello', 'Mixed content with a single value')
		e.add_child(structures.Element)
		try:
			e.get_value()
		except structures.GIFTMixedContentError:
			pass

	def test_copy(self):
		e1 = structures.Element(None)
		e2 = e1.deepcopy()
		self.assertTrue(isinstance(e2, structures.Element),
			"deepcopy didn't make Element")
		self.assertTrue(e1 == e2)
		self.assertTrue(e1 is not e2)


class DocumentTests(unittest.TestCase):
	def setUp(self):
		self.cwd = os.getcwd()
		self.d = mkdtemp('.d', 'pyslet-test_gift-')
		os.chdir(self.d)

	def tearDown(self):
		os.chdir(self.cwd)
		shutil.rmtree(self.d, True)

	def test_constructor(self):
		d = structures.Document()
		self.assertTrue(d.root is None, 'root on construction')
		self.assertTrue(d.get_base() is None, 'base set on construction')
		d = structures.Document(root=structures.Element)
		self.assertTrue(isinstance(d.root, structures.Element),
			'root not created on construction')
		self.assertTrue(d.root.get_document() is d,
			'root not linked to document')

	def test_base(self):
		"""Test the use of a file path on construction"""
		fpath = os.path.abspath('fpath.txt')
		furl = str(uri.URI.from_path(fpath))
		d = structures.Document(base_uri=furl)
		self.assertTrue(d.get_base() == furl, "Base not set in constructor")
		self.assertTrue(d.root is None, 'root on construction')
		d = structures.Document(base_uri='fpath.txt', root=structures.Element)
		self.assertTrue(d.get_base() == furl,
			"Base not made absolute from relative URL:\n\t%s\n\t%s" %
			(furl, d.get_base()))
		self.assertTrue(isinstance(d.root, structures.Element),
			'root not created on construction')
		d = structures.Document()
		d.set_base(furl)
		self.assertTrue(d.get_base() == furl, "Base not set by set_base")

	# def test_read_file(self):
	# 	"""Test the reading of the Document from the file system"""
	# 	os.chdir(TEST_DATA_DIR)
	# 	d = structures.Document(base_uri='readFile.txt')
	# 	d.read()
	# 	root = d.root
	# 	self.assertTrue(isinstance(root, structures.Element))
	# 	self.assertTrue(root.giftname == 'tag' and root.get_value() == 'Hello World')
	#
	# Cannot find where root is set to an Element in the source code, when
	# Document object instantiated with no root specified or d.read()
	# Need to implement parser still.

	# def test_read_string(self):
	# 	"""Test the reading of the Document from a supplied stream"""
	# 	os.chdir(TEST_DATA_DIR)
	# 	d = structures.Document(base_uri='readFile.txt')
	# 	f = open('readFile.txt', 'rb')
	# 	d.read(src=f)
	# 	f.close()
	# 	root = d.root
	# 	self.assertTrue(isinstance(root, structures.Element))
	# 	self.assertTrue(root.giftname == 'tag' and root.get_value() == 'Hello World')

	# def test_string(self):
	# 	os.chdir(TEST_DATA_DIR)
	# 	d = structures.Document(base_uri='readFile.txt')
	# 	d.read()
	# 	f = open('readFile.txt', 'rb')
	# 	flines = f.read().splitlines()
	# 	f.close()
	# 	# bytes always formats using unix-style newlines
	# 	dlines = bytes(d).split(b'\n')
	# 	self.assertTrue(dlines == flines, "GIFT output: %s" % bytes(d))
	# 	# requires implementing __bytes__ method which relies on generate_gift()

	def test_resolve_base(self):
		"""Test the use of a resolve_uri and resolve_base"""
		os.chdir(TEST_DATA_DIR)
		parent = structures.Element(None)
		self.assertTrue(parent.resolve_base() is None, "No default base")
		child = structures.Element(parent)
		self.assertTrue(child.resolve_base() is None, "No gift:base by default")
		parent.set_base('file:///index.txt')
		self.assertTrue(child.resolve_base() == 'file:///index.txt',
			"No gift:base inheritance")
		# Tests with a document follow
		furl = str(uri.URI.from_path(os.path.abspath('base.txt')))
		href = uri.URI.from_path(os.path.abspath('link.txt'))
		href_path = href.abs_path
		href = str(href)
		alt_ref = 'file:///hello/link.txt'
		d = structures.Document(base_uri='base.txt')
		self.assertTrue(d.get_base() == furl,
			"Base not resolved relative to w.d. by constructor")
		# TODO: implement parsing for unittests/data_gift/base.txt
		# d.read()
		# tag = d.root
		# self.assertTrue(
		# 	tag.resolve_base() == furl, "Root element resolves from document")

	# def test_create(self):
	# 	"""Test the creating of the Document on the file system."""
	# 	create_1_gift = ""
	# 	d = structures.Document(root=NamedElement)
	# 	d.set_base('create1.txt')
	# 	d.create()
	#   # create() depends on write_gift() method
	# 	try:
	# 		f = open("create1.txt")
	# 		data = f.read()
	# 		f.close()
	# 		self.assertTrue(data == create_1_gift, "create Test")
	# 	except IOError:
	# 		self.fail("create Test failed to create file")

	def test_update(self):
		pass

	def test_id(self):
		"""Tests the built-in handling of a Document's ID space."""
		doc = structures.Document()
		e1 = structures.Element(doc)
		e2 = structures.Element(doc)
		e1.id = e2.id = 'test'
		doc.register_element(e1)
		try:
			doc.register_element(e2)
			self.fail("Failed to spot ID clash")
		except structures.GIFTIDClashError:
			pass
		e2.id = 'test2'
		doc.register_element(e2)
		self.assertTrue(doc.get_element_by_id('test') is e1,
			"Element look-up failed")
		new_id = doc.get_unique_id('test')
		self.assertFalse(new_id == 'test' or new_id == 'test2')

	def test_reflection(self):
		pass

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	unittest.main()
