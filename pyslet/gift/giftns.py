#! /usr/bin/env python

"""
A namespace is an abstract container or environment created to hold a logical grouping
of unique identifiers or symbols (i.e. names).  An identifier defined in a namespace is
associated only with that namespace.

Namespaces are typically employed for the purpose of grouping symbols and identifiers
around a particular functionality and to avoid name collisions between multiple identifiers
that share the same name.

parser.py
structures.py

"""
import logging
import warnings

from .structures import (
	Document,
	DuplicateGIFTNAME,
	escape_char_data,
	Element,
	Node)

from .parser import (
	GIFTFatalError,
	GIFTParser)

#: Special string constant used to represent no namespace
NO_NAMESPACE = "~"


class GIFTNSError(GIFTFatalError):
	"""Raised when an illegal QName is found."""
	pass


def is_valid_ncname(name):
	"""Checks a string against NCName"""
	if name:
		# if not is_name_start_char(name[0]) or name[0] == ":":
		if not isinstance(name[0], str) or name[0] == ":":
			return False
		for c in name[1:]:
			# if not is_name_char(c) or c == ":":
			if not isinstance(name[0], str) or c == ":":
				return False
		return True
	else:
		return False


def attr_name_key(aname):
	"""A nasty function to make sorting attribute names predictable."""
	if isinstance(aname, str):
		return (NO_NAMESPACE, str(aname))
	else:
		return aname


class NSNode(Node):
	"""Base class for NSElement and Document shared attributes.

	This class adds a number of methods for managing the mapping
	between namespace prefixes and namespace URIs in both elements
	and in the document itself.

	You don't have to worry about using these, they are called
	automatically enabling the transparent serialisation of GIFT
	elements with appropriately defined namespace prefixes.  You
	only need to use these methods if you wish to customise the way
	the mapping is done.

	The most likely use case is simply to call :meth:`make_prefix`
	at the document level to add an explicit declaration of any
	auxiliary namespaces, typically done by the __init__ method on
	classes derived from NSDocument.
	"""
	def __init__(self, parent=None):
		self._prefix_to_ns = {}
		self._ns_to_prefix = {}
		super().__init__(parent)

	def reset_prefix_map(self, recursive=False):
		self._prefix_to_ns = {}
		self._ns_to_prefix = {}
		if recursive:
			for child in self.get_children():
				if not isinstance(child, str):
					child.reset_prefix_map(True)

	def get_prefix(self, ns):
		"""Returns the prefix assigned to a namespace

		ns
			The namespace URI as a character string.

		Returns None if no prefix is currently in force for this
		namespace.
		"""
		return None

	def get_ns(self, prefix=''):
		"""Returns the namespace associated with prefix.

		"""
		pass

	def new_prefix(self, stem='ns'):
		pass

	def make_prefix(self, ns, prefix=None):
		pass

	def get_prefix_map(self):
		pass

	def write_nsattrs(self, attributes, root=False, **kws):
		pass


class NSElement(NSNode, Element):
	"""Element class used for namespace-aware elements.

	Namespace aware elements have special handling for elements
	that contain namespace declarations and for handling qualified
	names.  A qualified name is a name that starts with a namespace
	prefix followed by a colon, for example "md:name" might represent
	the 'name' element in a particular namespace indicated by the
	prefix 'md'.

	The *same* element could equally be encountered with a different
	prefix depending on the namespace declarations in the document.
	As a result, to interpret element (and attribute) names they
	must be expanded.

	An expanded name is represented as a 2-tuple consisting of two
	character strings, the first is a URI of a namespace (used only as
	an identifier, the URI does not have to be the URI of an actual
	resource).  The second item is the element name defined within
	that namespace.

	In general, when dealing with classes derived from NSElement you
	should use expanded names wherever you would normally use a plain
	character string.  For example, the class attribute XMLNAME, used by
	derived classes to indicate the default name to use for the element
	the class represents must be an expanded name::

		class MyElement(NSElement):
			XMLNAME = ('http://www.example.com/namespace', 'MyElement')

	Custom attribute mappings use special class attributes with names
	starting with XMLATTR\_ and this mechanism cannot be extended to use
	the expanded names.  As a result these mappings can only be used for
	attributes that have no namespace.  In practice this is not a
	significant limitation as attributes are usually defined this way in
	XML documents.  Note that the special XML attributes (which appear
	to be in the namespace implicitly decared by the prefix "xml:")
	should be referenced using the special purpose get/set methods
	provided.
	"""
	def __init__(self, parent, name=None):
		super().__init__(parent)
		if name is not None:
			warnings.warn(
				"NSElement: passing name to constructor is deprecated(%s); "
				"use set_giftname instead" % name)
			import traceback
			traceback.print_stack()
			self.set_giftname(name)

	def set_giftname(self, name):
		"""Sets the name of this element

		Overridden to support setting the name from either an expanded name or
		an *unqualified* name (in which case the namespace is set to None).
		"""
		if isinstance(name, str):
			self.ns = None
			self.giftname = name
		elif name is None:
			self.ns = self.giftname = None
		else:
			self.ns, self.giftname = name

	def get_giftname(self):
		"""Returns the name of this element

		For classes derived from NSElement this is always an expanded name
		(even if the first component is None, indicating that the namespace
		is not known.)
		"""
		return (self.ns, self.giftname)

	@classmethod
	def mangle_aname(cls, name):
		pass

	@classmethod
	def unmangle_aname(cls, mname):
		pass

	def set_attribute(self, name, value):
		"""Sets the value of an attribute

		Overridden to allow attributes to be set using either expanded
		names (2-tuples) or *unqualified* names (character strings).

		Implementation notes: for elements descended from NSElement all
		attributes are stored using expanded names internally.  The
		method :meth:`unmangle_name` is overridden to return a 2-tuple
		to make their 'no namespace' designation explicit.

		This method also catches the new namespace prefix mapping for
		the element which is placed in a special attribute by
		:py:meth:`GIFTNSParser.parse_nsattrs` and updates the element's
		namespace mappings accordingly.
		"""
		if name == (NO_NAMESPACE, ".ns"):
			self._prefix_to_ns = nsMap = value
			self._ns_to_prefix = dict(
				(k, v) for (k, v) in
				zip(dict.values(nsMap), dict.keys(nsMap)))
			return
		elif (hasattr(self.__class__, 'ID') and
				(name == (NO_NAMESPACE, self.__class__.ID) or
					name == self.__class__.ID)):
			self.set_id(value)
		if isinstance(name, str):
			return Element.set_attribute(self, (NO_NAMESPACE, name), value)
		else:
			return Element.set_attribute(self, name, value)

	def get_attribute(self, name):
		"""Gets the value of an attribute.

		Overridden to allow attributes to be got using either expanded names
		(2-tuples) or *unqualified* names (character strings).
		"""
		if (hasattr(self.__class__, 'ID') and
			(name == (NO_NAMESPACE, self.__class__.ID) or
				name == self.__class__.ID)):
			# we have to override ID handling as mangling is special
			return self.id
		if isinstance(name, str):
			return Element.get_attribute(self, (NO_NAMESPACE, name))
		else:
			return Element.get_attribute(self, name)

	def is_valid_name(self, value):
		return is_valid_ncname(value)

	@staticmethod
	def sort_names(name_list):
		name_list.sort(key=attr_name_key)

	def write_gift_attributes(self, attributes, root=False, **kws):
		attrs = self.get_attributes()
		keys = sorted(dict.keys(attrs))
		for a in keys:
			if isinstance(a, str):
				logging.error(
					"Deprecation warning: found attribute with no namespace "
					"in NSElement, %s(%s)", self.__class__.__name__, a)
				aname = a
				prefix = ''
			else:
				ns, aname = a
				prefix = self.get_prefix(ns)
			if prefix is None:
				prefix = self.make_prefix(ns)
			if prefix:
				prefix = prefix + ':'
			attributes.append('%s%s=%s' % (prefix, aname, escape_char_data(attrs[a], True)))
		self.write_nsattrs(
			attributes, root=root)

	def generate_gift(self, indent='', tab='\t', root=False, **kws):
		if tab:
			ws = '\n' + indent
			indent = indent + tab
		else:
			ws = ''
		if not self.can_pretty_print():
			# inline all children
			indent = ''
			tab = ''
		attributes = []
		if self.ns:
			# look up the element prefix
			prefix = self.get_prefix(self.ns)
			if prefix is None:
				# We need to declare our namespace
				prefix = self.make_prefix(self.ns, '')
		else:
			prefix = ''
		if prefix:
			prefix = prefix + ':'
		self.write_gift_attributes(attributes, root=root)
		if attributes:
			attributes[0:0] = ['']
			attributes = ' '.join(attributes)
		else:
			attributes = ''
		children = self.get_canonical_children()
		# Need to fill in with gift generation


class NSDocument(Document, NSNode):
	default_ns = None
	"""The default namespace for this document class

	A special class attribute used to set the default namespace
	for elements create within the document that are parsed without
	an effective namespace declaration.  Set to None, but typically
	overridden by derived classes.
	"""
	def GIFTParser(self, entity):    # noqa
		"""Namespace documents use the special :py:class:`GIFTNSParser`.
		"""
		return GIFTNSParser(entity)

	def get_element_class(cls, name):
		"""Returns a class object suitable for representing <name>

		name is a tuple of (namespace, name), this overrides the
		behaviour of Document, in which name is a string.

		The default implementation returns NSElement.
		"""
		return NSElement


class GIFTNSParser(GIFTParser):
	"""A special parser for parsing documents that may use namespaces."""
	_nsdoc_class_table = {}

	@classmethod
	def register_nsdoc_class(cls, doc_class, xname):
		"""Registers a document class

		Internally GIFTNSParser maintains a single table of document classes
		which can be used to identify the correct class to use to represent
		a document based on the expanded name of the root element.

		doc_class
			the class object being registered, it must be derived from
			:py:class:`NSDocument`

		xname
			A tuple of (namespace, name) representing the name of the root
			element.  If either (or both) components are None a wildcard is
			registered that will match any corresponding value.
		"""
		cls._nsdoc_class_table[xname] = doc_class

	def get_nsdoc_class(self, xname):
		"""Returns a doc class object suitable for this root element

		xname
			An expanded name

		Returns a class object derived from :py:class:`NSDocument`
		suitable for representing a document with a root element with
		the given expanded name.

		This default implementation uses xname to locate a class
		registered with :meth:`register_nsdoc_class`.  If an exact match
		is not found then wildcard matches are tried matching *only* the
		namespace and root element name in turn.

		A wildcard match is stored in the mapping table either as an
		expanded name of the form (<uri string>, None) or (None,
		<element name>).  The former is preferred as it enables a
		document class to be defined that is capable of representing a
		document with any root element from the given namespace (a
		common use case) and is thus always tried first.

		If no document class can be found, :py:class:`NSDocument` is
		returned.
		"""
		if xname[0] is None:
			doc_class = GIFTParser._nsdoc_class_table.get(xname, None)
		else:
			doc_class = GIFTParser._nsdoc_class_table.get(xname, None)
			if doc_class is None:
				doc_class = GIFTParser.DocumentClassTable.get(
					(xname[0], None), None)
			if doc_class is None:
				doc_class = GIFTParser.DocumentClassTable.get(
					(None, xname[1]), None)
		if doc_class is None:
			doc_class = NSDocument
		return doc_class

	def __init__(self, entity=None):
		GIFTParser.__init__(self, entity)

	def expand_qname(self):
		pass

	def match_gift_name(self, element, qname):
		pass

	def parse_nsattrs(self, attrs):
		"""Manges namespace prefix mappings

		Takes a dictionary of attributes as returned by
		:meth:`parse_stag` and finds any namespace prefix mappings
		returning them as a dictionary of prefix:namespace suitable for
		passing to :py:meth:`expand_qname`.  It also removes the
		namespace declarations from attrs and expands the attribute
		names into (ns, name) pairs.

		Implementation note: a special attribute called '.ns' (in no
		namespace) is set to the parsed prefix mapping dictionary
		enabling the prefix mapping to be passed transparently to
		:py:meth:`NSElement.set_attribute` by py:class:`GIFTParser`.
		"""
		pass

	def get_stag_class(self):
		pass


def map_class_elements(class_map, scope, ns_alias_table=None):
	"""
	Usage:
	https://github.com/swl10/pyslet/blob/master/pyslet/qtiv2/xml.py#L74
	xmlns.map_class_elements(QTIDocument.classMap, variables)
	xmlns.map_class_elements(QTIDocument.classMap, processing)
	xmlns.map_class_elements(QTIDocument.classMap, content)
	xmlns.map_class_elements(QTIDocument.classMap, interactions)
	xmlns.map_class_elements(QTIDocument.classMap, items)
	xmlns.map_class_elements(QTIDocument.classMap, tests)
	xmlns.map_class_elements(QTIDocument.classMap, expressions)
	xmlns.map_class_elements(QTIDocument.classMap, metadata)

	Adds element name -> class mappings to class_map

	class_map
		A dictionary that maps element *expanded* names onto class
		objects.

	scope
		A dictionary, or an object containing a __dict__ attribute, that
		will be scanned for class objects to add to the mapping.  This enables
		scope to be a module.  The search is not recursive, to add class elements
		from imported modules you must call map_class_elements for each module.

	ns_alias_table
		Used to create multiple mappings for selected element classes based on namespace aliases.
		It is a dictionary mapping a canonical namespace to a list of aliases.  For example, if::

			ns_alias_table={'http://www.example.com/schema-v3': [
								'http://www.example.com/schema-v2',
								'http://www.example.com/schema-v1']}

		An element class with::

			XMLNAME = ('http://www.example.com/schema-v3', 'data')

		would then be used by the parser to represent the <data> element
		in the v1, v2 and v3 schema variants.

	The scope is searched for classes derived from :py:class:`NSElement`
	that have a GIFTNAME attribute defined.  It is an error if a class is found
	with a GIFTNAME that has already been mapped.
	"""
	if not isinstance(scope, dict):
		scope = scope.__dict__
	for name in dict.keys(scope):
		obj = scope[name]
		if issubclass(type(obj), type) and issubclass(obj, NSElement):
			if hasattr(obj, 'GIFTNAME'):
				if obj.GIFTNAME in class_map:
					raise DuplicateGIFTNAME(
						"%s and %s has matching GIFTNAMEs" %
						(obj.__name__, class_map[obj.GIFTNAME].__name__))
				class_map[obj.GIFTNAME] = obj
				if ns_alias_table:
					aliases = ns_alias_table.get(obj.GIFTNAME[0], ())
					for alias in aliases:
						alias_name = (alias, obj.GIFTNAME[1])
						if alias_name in class_map:
							raise DuplicateGIFTNAME(
								"%s and %s have matching GIFTNAME alias %s" %
								(obj.__name__, class_map[obj.GIFTNAME].__name__, alias_name))
						class_map[alias_name] = obj


def match_expanded_names(xname, xmatch, ns_aliases=None):
	"""Compares two expanded names

	"""
	pass


def register_nsdoc_class(doc_class, expanded_name):
	GIFTNSParser.register_nsdoc_class(doc_class, expanded_name)
