#! /usr/bin/env python
import logging

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

		# Ignore unicode and sgml.  sgml refers to case insensitive.
		# See https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L651
		# for SGML's NAMECASE GENERAL for XML parser

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

	def _get_buff(self):
		if len(self.buff) > 1:
			return ''.join(self.buff[1:])
		else:
			return ''

	def push_entity(self, entity):
		"""Starts parsing an entity

		entity
			A :py:class:'~pyslet.gift.structures.GIFTEntity'
			instance which is to be parsed.

		:py:attr:`the_char` is set to the current character in the
		entity's stream.  The current entity is pushed onto an internal
		stack and will be resumed when this entity has been parsed
		completely.

		Note that in the degenerate case where the entity being pushed
		is empty (or is already positioned at the end of the file) then
		push_entity does nothing.
		"""
		if entity.the_char is not None:
			self.entityStack.append(self.entity)
			self.entity = entity
			self.entity.flags = {}
			self.the_char = self.entity.the_char
			# assume UTF-8 and ignore check for UTF-16
		if entity.buff_text:
			self.buff_text(entity.buff_text)

	def get_external_entity(self):
		"""Returns the external entity currently being parsed.

		If no external entity is being parsed then None is returned."""
		if self.entity.is_external():
			return self.entity
		else:
			i = len(self.entityStack)
			while i:
				i = i - 1
				e = self.entityStack[i]
				if e.is_external():
					return e
		return None

	def standalone(self):
		"""True if the document should be treated as standalone.

		A document may be declared standalone or it may effectively be
		standalone due to the absence of a DTD, or the absence of an
		external DTD subset and parameter entity references.
		"""
		if self.declared_standalone():
			return True
		if self.dtd is None or self.dtd.external_id is None:
			# no dtd or just an internal subset
			return not self.gotPERef

	def declared_standalone(self):
		"""True if the current document was declared standalone."""
		return self.declaration and self.declaration.standalone

	def well_formedness_error(self, msg="well-formedness error", error_class=GIFTWellFormedError):
		"""Raises a GIFTWellFormedError error.

		msg
			An optional message string

		error_class
			An optional error class which must be a class object derived from
			:py:class:`GIFTWellFormednessError`.

		Called by the parsing methods whenever a well-formedness constraint is violated.

		The method raises an instance of *error_class* and does not return.  This method
		can be overridden by derived parsers to implement more sophisticated error logging.
		"""
		raise error_class("%s: %s" % (self.entity.get_position_str(), msg))

	def validity_error(self, msg="validity error", error=gift.GIFTValidityError):
		"""Called when the parser encounters a validity error.

		msg
			An optional message string

		error
			An optional error class or instance which must be a (class)
			object derived from :py:class:`GIFTValidityError`.

		The behaviour varies depending on the setting of the :py:attr:`check_validity` and
		:py:attr:`raiseValidityErrors` options.  The default (both False) causes validity
		errors to be ignored.  When checking validity an error message is logged to
		:py:attr:`nonFatalErrors` and :py:attr:`valid` isset to False.  Furthermore, if
		:py:attr:`raiseValidityErrors` is True *error* is raised (or a new instance of *error*
		is raised) and parsing terminates

		This method can be overridden by derived parsers to implement more sophisticated
		error logging.
		"""
		if self.check_validity:
			self.valid = False
			if isinstance(error, gift.GIFTValidityError):
				self.nonFatalErrors.append(
					"%s: %s (%s)" %
					(self.entity.get_position_str(), msg, str(error)))
				if self.raiseValidityErrors:
					raise error
			elif issubclass(error, gift.GIFTValidityError):
				msg = "%s: %s" % (self.entity.get_position_str(), msg)
				self.nonFatalErrors.append(msg)
				if self.raiseValidityErrors:
					raise error(msg)
			else:
				raise TypeError(
					"validity_error expected class or instance of "
					"GIFTValidityError (found %s)" % repr(error))

	def compatibility_error(self, msg="compatibility error"):
		"""Called when the parser encounters a compatibility error.

		msg
			An optional message string

		The behaviour varies depending on the setting of the :py:attr:`checkCompatibility`
		flag.  The default (False) causes compatibility errors to be ignored.  When checking
		compatibility an error message is logged to :py:attr:`nonFatalErrors`.

		This method can be overridden by derived parsers to implement more sophisticated error
		logging.
		"""
		if self.checkCompatibility:
			self.nonFatalErrors.append(
				"%s: %s" % (self.entity.get_position_str(), msg))

	def processing_error(self, msg="Processing error"):
		"""Called when the parser encounters a general processing error.

		msg
			An optional message string

		The behaviour varies depending on the setting of the :py:attr:`checkAllErrors`
		flag.  The default (False) causes processing errors to be ignored.  When checking
		all errors an error message is logged to :py:attr:`nonFatalErrors`.

		This method can be overridden by derived parsers to implement more sophisticated error
		logging.
		"""
		if self.checkAllErrors:
			self.nonFatalErrors.append("%s: %s" % (self.entity.get_position_str(), msg))

	def parse_literal(self, match):
		"""Parses an optional literal string.

		match
			The literal string to match

		Returns True if *match* is successfully parsed and False otherwise.  There is no
		partial matching, if *match* is not found then the parser is left in its original
		position.
		"""
		match_len = 0
		for m in match:
			if m != self.the_char and (self.the_char is None or m.lower() != self.the_char.lower()):
				self.buff_text(match[:match_len])
				break
			match_len += 1
			self.next_char()
		return match_len == len(match)

	def parse_required_literal(self, match, production="Literal String"):
		"""Parses a required literal string.

		match
			The literal string to match

		production
			An optional string describing the context in which the literal was expected.

		There is no return value.  If the literal is not matched a wellformed error
		is generated.
		"""
		if not self.parse_literal(match):
			self.well_formedness_error("%s: Expected %s" % (production, match))

	def parse_decimal_digits(self):
		"""Parses a, possibly empty, string of decimal digits.

		Decimal digits match [0-9].  Returns the parsed digits as a string or
		an *empty string* if no digits were matched.
		"""
		data = []
		while self.the_char is not None and self.the_char in "0123456789":
			data.append(self.the_char)
			self.next_char()
		return ''.join(data)

	def parse_required_decimal_digits(self, production="Digits"):
		"""Parses a required string of decimal digits.

		production
			An optional string describing the context in which the
			decimal digits were expected.

		Decimal digits match [0-9].  Returns the parsed digits as a string.
		"""
		digits = self.parse_decimal_digits()
		if not digits:
			self.well_formedness_error(production + ": Expected [0-9]+")
		return digits

	def parse_hex_digits(self):
		raise NotImplementedError

	def parse_required_hex_digits(self, production="Hex Digits"):
		raise NotImplementedError

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
		self.refMode == GIFTParser.RefModeInContent
		self.doc = doc
		if self.checkAllErrors:
			self.checkCompatibility = True
		if self.checkCompatibility:
			self.check_validity = True
		if self.check_validity:
			self.valid = True
		else:
			self.valid = None
		self.nonFatalErrors = []
		# self.parse_prolog()
		if self.doc is None:
			raise gift.GIFTFatalError("parse_document(): self.doc is None")
		self.parse_element()
		self.parse_misc()
		if self.the_char is not None and not self.dont_check_wellformedness:
			self.well_formedness_error("Unparsed characters in entity after document: %s" %
				repr(self.the_char))
		return self.doc

	def get_document_class(self, dtd):
		"""
		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1176
		"""
		raise NotImplementedError

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

	def parse_entity_value(self):
		raise NotImplementedError

	def parse_system_literal(self):
		raise NotImplementedError

	def parse_comment(self, got_literal=False):
		"""[15] Comment

		got_literal
			If True then the method assumes that the '//' literal has
			already been parsed.

		Returns the comment as a string.
		"""
		production = "[15] Comment"
		data = []
		# nhyphens = 0
		if not got_literal:
			self.parse_required_literal('//', production)
		# centity = self.entity
		while self.the_char is not None:
			if self.the_char == '\n':
				# end of comment
				self.next_char()
				break
			else:
				data.append(self.the_char)
				self.next_char()
		return ''.join(data)

	def parse_prolog(self):
		# only relevant for XML documents
		raise NotImplementedError

	def parse_decl(self, got_literal=False):
		# only relevant for XML documents
		raise NotImplementedError

	def parse_misc(self):
		"""[27] Misc

		This method parses everything that matches the production Misc*
		"""
		while True:
			if self.is_s():
				self.next_char()
				continue
			elif self.parse_literal('//'):
				self.parse_comment(True)
				continue
			else:
				break

	def parse_int_subset(self):
		"""[28b] intSubset

		Parses an internal subset."""
		raise NotImplementedError

	def parse_markup_decl(self, got_literal=False):
		""" for xml, tag is '<'
		"""
		raise NotImplementedError

	def parse_ext_subset(self):
		""" external subset.  for xml, denoted with '<?xml'
		"""
		raise NotImplementedError

	def check_pe_between_declarations(self, check_entity):
		""" check well-formedness constraint on use of PEs between declarations.
		"""
		raise NotImplementedError

	def parse_element(self):
		"""[39] element

		The class used to represent the element is determined by calling the
		:py:meth:`~pyslet.gift.structures.Document.get_element_class`
		method of the current document.  If there is no document yet then a
		new document is created automatically (see :py:meth:`parse_document` for
		more information).

		The element is added as a child of the current element using
		:py:meth:`Node.add_child`.

		The method returns a boolean value:

		True
			the element was parsed normally

		False
			the element is not allowed in this context

		The second case only occurs when the :py:attrs:`sgml_omittag` option is
		in use and it indicates that the content of the enclosing element has ended.
		The Tag is buffered so that it can be reparsed when the stack of nested
		:py:meth:`parse_element` calls is unwound to the point where it is allowed
		by the context.
		"""
		production = "[39] element"
		save_element = self.element
		save_element_type = self.elementType
		save_cursor = None

		context = self.get_context()
		empty = False
		# get_context() returns either element or doc
		# Document.add_child(self, child_class, name=None)
		self.element = context.add_child(gift.Element, None)
		if getattr(gift.Element, 'GIFTCONTENT', gift.GIFTMixedContent) == gift.GIFTEmpty:
			empty = True
		if not empty:
			save_data_count = self.dataCount
			self.parse_content()
		if self.dataCount == save_data_count:
			raise gift.GIFTFatalError(production + ": element had empty content %s" % self.element)
		self.element.content_changed()
		self.element = save_element
		self.elementType = save_element_type
		self.cursor = save_cursor
		return True

	def check_attributes(self, name, attrs):
		""" Checks *attrs* against the declarations for an element.
		"""
		raise NotImplementedError

	def match_gift_name(self, element, name):
		""" tests if *name* is a possible name for *element*

		Checks if end tag is end tag of this element
		"""
		return element.get_giftname() == name

	def check_expected_particle(self, name):
		""" checks validity of element name in current context
		"""
		raise NotImplementedError

	def get_stag_class(self, name, attrs=None):
		raise NotImplementedError

	def parse_stag(self):
		""" [40] STag, [44] EmptyElemTag

		This method returns a tuple of (name, attrs, emptyFlag) where:

		name
			the name of the element parsed

		attrs
			a dictionary of attribute values keyed by attribute name

		emptyFlag
			a boolean; True indicates that the tag was an empty element tag.

		GIFT doesn't have element names nor attributes
		"""
		raise NotImplementedError

	def parse_attribute(self):
		raise NotImplementedError

	def parse_content(self):
		"""[43] content

		The method returns:

		True
			indicates that the content was parsed normally

		False
			indicates that the content contained data or markup not
			allowed in this context
		"""
		while True:
			if self.the_char == '/':
				# First character of comment tag
				self.next_char()
				if self.the_char == '/':
					# Second character of comment tag
					self.parse_comment(True)
				else:
					self.well_formedness_error("Expected Comment")
			elif self.the_char is '/n' or self.the_char is None:
				# end of entity
				return True
		return True

	def handle_data(self, data):
		"""[43] content

		data
			A string of data to be handled

		Data is handled by calling :py:meth:`~pyslet.gift.structures.Element.add_data`
		even if the data is optional white space.
		"""
		if data and self.element:
			self.element.add_data(data)
			self.dataCount += len(data)

	def unhandled_data(self, data):
		""" Only called when sgml_omittag option is in use.
		"""
		raise NotImplementedError

	def parse_empty_elem_tag(self):
		raise NotImplementedError

	def parse_content_spec(self, etype):
		raise NotImplementedError

	def parse_children(self):
		raise NotImplementedError

	def parse_cp(self):
		"""GIFTContentParticle"""
		raise NotImplementedError

	def parse_choice(self):
		raise NotImplementedError

	def parse_seq(self):
		raise NotImplementedError

	def parse_mixed(self):
		raise NotImplementedError
