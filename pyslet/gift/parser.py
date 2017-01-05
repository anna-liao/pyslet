#! /usr/bin/env python

from pyslet.gift import structures as gift
from ..pep8 import PEP8Compatibility


class GIFTFatalError(gift.GIFTError):
	"""Raised by a fatal error in the parser."""
	pass


class GIFTWellFormedError(GIFTFatalError):
	"""Raised when a well-formedness error is encountered."""
	pass


class GIFTForbiddenEntityReference(GIFTFatalError):
	"""Raised when a forbidden entity reference is encountered."""
	pass


def is_white_space(data):
	"""Tests if every character in *data* matches S"""
	for c in data:
		if not gift.is_s(c):
			return False
	return True


def contains_s(data):
	"""Tests if data contains any S characters"""
	for c in data:
		if gift.is_s(c):
			return True
	return False


def strip_leading_s(data):
	"""Returns data with all leading S removed."""
	s = 0
	for c in data:
		if gift.is_s(s):
			s += 1
		else:
			break
	if s:
		return data[s:]
	else:
		return data


def normalize_space(data):
	"""Implements attribute value normalization

	Returns data normalized according to the further processing rules
	for attribute-value normalization:

		"...by discarding any leading and trailing space characters, ..."
	"""
	pass


class ContentParticleCursor(object):
	"""Used to traverse an element's content model.

	The cursor records its position within the content model by
	recording the list of particles that may represent the current child
	element. When the next start tag is found the particles' maps are
	used to change the position of the cursor.  The end of the content
	model is represented by a special entry that maps the empty string
	to None.

	"""
	def __init__(self, element_type):
		pass

	def next(self, name=''):
		"""Called when a child element with *name* is encountered.
		"""
		pass

	def expected(self):
		"""Sorted list of valid element names in the current state.
		"""


class GIFTParser(PEP8Compatibility):

	"""A GIFTParser object

	entity
		The :py:class:`~pyslet.gift.structures.GIFTEntity` to parse.

	GIFTParser objects are used to parse entities for the constructs
	defined by the numbered productions in the GIFT specifiction.

	GIFTParser has a number of optional attributes, all of which default
	to False.  Attributes with names starting with 'check' increase the
	strictness of the parser.  All other parser flags, if set to True,
	will not result in a conforming GIFT processor."""

	_doc_class_table = {}
	"""A dictionary mapping doctype parameters onto class objects.

	For more information about how this is used see
	:py:meth:`get_document_class` and :py:meth:`register_doc_class`."""

	@classmethod
	def register_doc_class(cls, doc_class, root_name, public_id=None, system_id=None):
		"""Registers a document class

		Internally GIFTParser maintains a single table of document
		classes which can be used to identify the correct class to use to represent
		a document based on the information obtained from the DTD.

		doc_class
			the class object being registered, it must be derived from
			:py:class:`Document`

		root_name
			the name of the root element or None if this class can be used with any
			root element

		public_id
			the optional public ID of the doctype, if None or omitted any doctype
			can be used with this document class

		system_id
			the optional system ID of hte doctype, if None or omitted (the usual case)
			the document class can match any system ID.
		"""
		pass

	#: Default constant used for setting :py:attr:`refMode`
	RefModeNone = 0

	#: Treat references as per "in Content" rules
	RefModeInContent = 1

	#: Treat references as per "in Attribute Value" rules
	RefModeInAttributeValue = 2

	#: Treat references as per "as Attribute Value" rules
	RefModeAsAttributeValue = 3

	#: Treat references as per "in EntityValue" rules
	RefModeInEntityValue = 4

	def __init__(self, entity):
		"""
		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L622
		"""
		PEP8Compatibility.__init__(self)
		self.check_validity = False
		"""Checks GIFT validity constraints

		If *check_validity* is True, and all other options are left at their
		default (False) setting then the parser will behave as a validating
		GIFT parser.
		"""

		#: Flag indicating if the document is valid, only set if
		#: :py:attr:`check_validity` is True
		self.valid = None
		#: A list of non-fatal errors discovered during parsing, only
		#: populated if :py:attr:`check_validity` is True
		self.nonFatalErrors = []
		#: checks GIFT compatibility constraints; will cause
		#: :py:attr:`check_validity` to be set to True when parsing
		self.checkCompatibility = False
		#: checks all constraints; will cause :py:attr:`check_validity`
		#: and :py:attr:`checkCompatibility` to be set to True when
		#: parsing.
		self.checkAllErrors = False
		#: treats validity errors as fatal errors
		self.raiseValidityErrors = False
		#: provides a loose parser for GIFT-like documents
		self.dont_check_wellformedness = False

		self.refMode = GIFTParser.RefModeNone
		"""The current parser mode for interpreting references.

		GIFT documents can contain five different types of reference:
		parameter entity, internal general entity, external parsed
		entity, (external) unparsed entity and character entity.

		The rulse for interpreting these references vary depending on
		the current mode of the parser.  For example, in content a
		reference to an internal entity is replaced, but in the
		definition of an entity value it is not.  This means that the
		behaviour of the :py:meth:`parse_reference` method will differ
		depending on the mode.

		The parser takes care of setting the mode automatically but if
		you wish to use some of the parsing methods in isolation to parse
		fragments of GIFT documents, then you will need to set the
		*refMode* directly using one of the RefMode* family of
		constants defined above.
		"""
		#: The current entity being parsed
		self.entity = entity
		self.entityStack = []
		if self.entity:
			#: the current character; None indicates end of stream
			self.the_char = self.entity.the_char
		else:
			self.the_char = None
		self.buff = []
		#: The document being parsed
		self.doc = None
		#: The document entity
		self.docEntity = entity
		#: The current element being parsed
		self.element = None
		#: The element type of the current element
		self.elementType = None
		self.idTable = {}
		self.idRefTable = {}
		self.cursor = None
		self.dataCount = 0
		self.noPERefs = False
		self.gotPERef = False

	def get_context(self):
		"""Returns the parser's context

		This is either the current element or the document if no
		element is being parsed.
		"""
		if self.element is None:
			return self.doc
		else:
			return self.element

	def next_char(self):
		"""Moves to the next character in the stream.

		The current character can always be read from
		:py:attr:`the_char`.  If there are no characters
		left in the current entity then entities are
		popped from an internal entity stack automatically.
		"""
		if self.buff:
			self.buff = self.buff[1:]
		if self.buff:
			self.the_char = self.buff[0]
		else:
			self.entity.next_char()
			self.the_char = self.entity.the_char
			while self.the_char is None and self.entityStack:
				self.entity.close()
				self.entity = self.entityStack.pop()
				self.the_char = self.entity.the_char

	def buff_text(self, unused_chars):
		pass

	def parse_document(self, doc=None):
		""" [1] document: parses a Document.

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1126

		doc
			The :py:class:`~pyslet.gift.structures.Document`
			instance that will be parsed.  The declaration, dtd and
			elements are added to this document.  If *doc* is None then
			a new instance is created using :py:meth:`get_document_class`
			to identify the ocrrect class to use to represent the document
			based on information in the prolog or, if the prolog lacks a
			declaration, the root element.

		This method returns the document that was parsed, an instance of
		:py:class:`~pyslet.gift.structures.Document`.
		"""
		pass

	def get_document_class(self, dtd):
		"""
		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1176
		"""
		pass

	def is_s(self):
		"""Tests if the current character matches S

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1241

		returns a boolean value, True if S is matched.

		By default calls :py:func:`~pyslet.gift.structures.is_s`
		"""
		return gift.is_s(self.the_char)

	def parse_s(self):
		"""[3] S

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1258

		Parses white space returning it as a string.  If there is no white space
		at the current position then an *empty string* is returned.

		NOTE: did not include unicodecompatibility code from qtiv2, because this
		module is written for Python 3.  All Python 3 string are unicode.
		"""
		s = []
		slen = 0
		while True:
			if self.is_s():
				s.append(self.the_char)
				self.next_char()
			#: does not check for unicodecompatibility
			else:
				break
			slen += 1
		return ''.join(s)

	def parse_required_literal(self, match, production="Literal String"):
		"""Parses a required literal string.

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1039

		match
			The literal string to match

		production
			An optional string describing the context in which the literal was
			expected.

		There is no return value.  If the literal is not matched a wellformed
		error is generated.
		"""
		if not self.parse_literal(match):
			self.well_formedness_error("%s: Expected %s" % (production, match))

	def parse_literal(self, match):
		"""Parses an optional literal string.

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1019

		match
			The literal string to match

		Returns True if *match* is successfully parse and False otherwise.
		There is no partial matching, if *match* is not found then the parser
		is left in its original position.
		"""
		match_len = 0
		for m in match:
			if m != self.the_char and (self.the_char is None or
				m.lower() != self.the_char.lower()):
				self.buff_text(match[:match_len])
				break
			match_len += 1
			self.next_char()
		return match_len == len(match)

	def well_formedness_error(self, msg="well-formedness error", error_class=GIFTWellFormedError):
		"""Raises a GIFTWellFormedError error.

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L924

		msg
			An optional message string

		error_class
			an optional error class which must be a class object derived
			from py:class:`GIFTWellFormedError`.

		Called by the parsing methods whenever a well-formedness constraint is violated.

		The method raises an instance of *error_class* and does not return.  This method
		can be overridden by derived parsers to implement more sophisticated error logging.
		"""
		raise error_class("%s: %s" % (self.entity.get_position_str(), msg))

	def next_char(self):
		"""Moves to the next character in the stream.

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L764

		The current character can always be read from :py:attr:`the_char`. If
		there are no characters left in the current entity then entities are
		popped from an internal entity stack automatically.
		"""
		if self.buff:
			self.buff = self.buff[1:]
		if self.buff:
			self.the_char = self.buff[0]
		else:
			self.entity.next_char()
			self.the_char = self.entity.the_char
			while self.the_char is None and self.entityStack:
				self.entity.close()
				self.entity = self.entityStack.pop()
				self.the_char = self.entity.the_char

	def buff_text(self, unused_chars):
		"""Buffers characters that have already been parsed.

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L783

		unused_chars
			A string of characters to be pushed back to the parser in the order
			in which they are to be parsed.

		This method enables characters to be pushed back into the parser forcing
		them to be parsed next.  The current character is saved and will be parsed
		(again) once the buffer is exhausted.
		"""
		if unused_chars:
			if self.buff:
				self.buff = list(unused_chars) + self.buff
			else:
				self.buff = list(unused_chars)
				if self.entity.the_char is not None:
					self.buff.append(self.entity.the_char)
				self.the_char = self.buff[0]

	def parse_comment(self, got_literal=False):
		""" [15] Comment

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1597

		got_literal
			If True then the method assumes that the '//' literal has already
			been parsed.

		qti comment is '<!--'

		GIFT line comment: https://docs.moodle.org/23/en/GIFT_format#Line_Comments

		Returns the comment as a string.
		"""

		production = "[15] Comment"
		data = []
		if not got_literal:
			self.parse_required_literal('//', production)
		while self.the_char is not None:
			"""Iterates through each character.

			Example of GIFT format:
			// question: 914  name: What's 2 plus 2?
			::What's 2 plus 2?::What's 2 plus 2?{#
				=4:0#
			}

			Comments start with "//" and ends at the end of the line
			"""
			if self.the_char == 'EOL':
				#: Need to figure out how end of line character is defined
				pass
			else:
				data.append(self.the_char)
				self.next_char()
		return ''.join(data)


