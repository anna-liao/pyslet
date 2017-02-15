#! /usr/bin/env python
import logging

from pyslet.gift import structures as gift
from ..pep8 import PEP8Compatibility
from .py3 import dict_keys


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

	START_STATE = 0     #: State constant representing the start state
	PARTICLE_STATE = 1  #: State constant representing a particle
	END_STATE = 2       #: State constant representing the end state

	def __init__(self, element_type):
		self.element_type = element_type
		self.state = ContentParticleCursor.START_STATE
		self.plist = []

	def next(self, name=''):
		"""Called when a child element with *name* is encountered.

		Returns True if *name* is a valid element and advances the
		model.  If *name* is not valid then it returns False and the
		cursor is unchanged.
		"""
		if self.state == ContentParticleCursor.START_STATE:
			if self.element_type.particle_map is not None:
				if name in self.element_type.particle_map:
					self.plist = self.element_type.particle_map[name]
					if self.plist is None:
						self.state = ContentParticleCursor.END_STATE
					else:
						if not isinstance(self.plist, list):
							self.plist = [self.plist]
						self.state = ContentParticleCursor.PARTICLE_STATE
					return True
				else:
					return False
			elif self.element_type.content_type == gift.ElementType.ANY:
				# anything goes for an ANY element, we stay in the start state
				if not name:
					self.state = ContentParticleCursor.END_STATE
				return True
			elif self.element_type.content_type == gift.ElementType.EMPTY:
				# empty elements, or unparsed elements
				if not name:
					self.state = ContentParticleCursor.END_STATE
					return True
				else:
					return False
			elif self.state == ContentParticleCursor.PARTICLE_STATE:
				new_plist = []
				for p in self.plist:
					# go through all possible particles
					if name in p.particle_map:
						ps = p.particle_map[name]
						if ps is None:
							# short cut to end state
							new_plist = None
							self.state = ContentParticleCursor.END_STATE
							break
						if isinstance(ps, list):
							new_plist = new_plist + ps
						else:
							new_plist.append(ps)
				if new_plist is None or len(new_plist) > 0:
					# success if we got to the end state or have found particles
					self.plist = new_plist
					return True
				else:
					return False
			else:
				# when in the end state everything is invalid
				return False

	def expected(self):
		"""Sorted list of valid element names in the current state.
		"""
		expected = {}
		end_tag = None
		if self.state == ContentParticleCursor.START_STATE:
			for name in dict_keys(self.element_type.particle_map):
				if name:
					expected[name] = True
				else:
					end_tag = "</%s>" % self.element_type.name
		elif self.state == ContentParticleCursor.PARTICLE_STATE:
			for p in self.plist:
				for name in dict_keys(p.particle_map):
					if name:
						expected[name] = True
					else:
						end_tag = "</%s>" % self.element_type.name
		result = sorted(dict_keys(expected))
		if end_tag:
			result.append(end_tag)
		return result


# class GIFTParser(PEP8Compatibility):
class GIFTParser:

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
		raise NotImplementedError

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
		# PEP8Compatibility.__init__(self)
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

		self.in_comment = False
		self.in_question = False
		self.parse_question_title = False
		self.in_question_title = False
		self.in_responses = False
		self.in_correct_response = False
		self.in_wrong_response = False
		self.after_brackets = False
		self.numericType = False
		self.booleanType = False
		self.first_response = False

	def reset(self):
		self.in_comment = False
		self.in_question = False
		self.parse_question_title = False
		self.in_question_title = False
		self.in_responses = False
		self.in_correct_response = False
		self.in_wrong_response = False
		self.in_boolean = False
		self.after_brackets = False
		self.numericType = False
		self.booleanType = False
		self.first_response = False

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
		if isinstance(self.the_char, int):
			self.the_char = chr(self.the_char)

	def buff_text(self, unused_chars):
		"""Buffers characters that have already been parsed.

		unused_chars
			A string of characters to be pushed back to the parser in
			the order in which they are to be parsed.

		The method enables characters to be pushed back into the parser
		forcing them to be parsed next.  The current character is saved
		and will be parsed (again) once the buffer is exhausted.
		"""
		if unused_chars:
			if self.buff:
				self.buff = list(unused_chars) + self.buff
			else:
				self.buff = list(unused_chars)
				if self.entity.the_char is not None:
					self.buff.append(self.entity.the_char)
			self.the_char = self.buff[0]

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
		if isinstance(self.the_char, int):
			self.the_char = chr(self.the_char)
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
			if self.dtd.name is not None:
				# create the document based on information in the DTD
				self.doc = self.get_document_class(self.dtd)()
				# set the document's dtd
				self.doc.dtd = self.dtd
		elif self.doc.dtd is None:
			# override the document's DTD
			self.doc.dtd = self.dtd
		# self.parse_element()
		self.parse_content()
		if self.check_validity:
			for idref in dict_keys(self.idRefTable):
				if idref not in self.idTable:
					self.validity_error("IDREF: %s does not match any ID attribute value")
		# self.parse_misc()
		if self.the_char is not None and not self.dont_check_wellformedness:
			self.well_formedness_error("Unparsed characters in entity after document: %s" %
				repr(self.the_char))
		return self.doc

	def get_document_class(self, dtd):
		"""Returns a class object suitable for this dtd

		dtd
			A :py:class:`~pyslet.xml.structures.XMLDTD` instance
		
		"""

	def is_s(self):
		"""Tests if the current character matches S

		https://github.com/swl10/pyslet/blob/master/pyslet/xml/parser.py#L1241

		returns a boolean value, True if S is matched.

		By default calls :py:func:`~pyslet.gift.structures.is_s`
		"""
		if isinstance(self.the_char, int):
			return gift.is_s(chr(self.the_char))
		else:
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

	def parse_required_s(self, production="[3] S"):
		"""[3] S: Parses required white space

		production
			An optional string describing the production being parsed.
			This allows more useful errors than simple 'expected [3] S'
			to be logged.

		If there is no white space then a well-formedness error is raised.
		"""
		if not self.parse_s() and not self.dont_check_wellformedness:
			self.well_formedness_error(production + ": Expected white space character")

	def parse_name(self):
		# raise NotImplementedError
		return None

	def parse_required_name(self):
		return None

	def parse_names(self):
		raise NotImplementedError

	def parse_entity_value(self):
		"""[9] EntityValue

		Parses an EntityValue, returning it as a string.

		This method automatically expands other parameter entity references but does not
		expand general or character references.

		I *think* this handles references in the XML format that is not relevant in the
		GIFT format.  It calls parse_quote(), and quotes are not special escape characters
		in GIFT.
		"""
		# save_mode = self.refMode
		# qentity = self.entity
		# q = self.parse_quote()
		raise NotImplementedError

	def parse_system_literal(self):
		"""value of literal returned as string *without* enclosing quotes.
		Not relevant for GIFT format."""
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

	control_chars = ('~', '=', '#', '}')


	def parse_question_title(self, got_literal=False):
		""" ::Question title::
		"""
		raise NotImplementedError
		# production = "Question Title"
		# save_element =
		# data = []
		# if not got_literal:
		# 	self.parse_required_literal('::', production)
		# while self.the_char is not None:
		# 	if self.the_char in control_chars:
		# 		self.next_char()
		# 		break
		# 	else:
		# 		data.append(self.the_char)
		# 		self.next_char()
		# return ''.join(data)

	def parse_question(self, got_literal=False):
		raise NotImplementedError

	def parse_correct_response(self, got_literal=False):
		raise NotImplementedError

	def parse_wrong_response(self, got_literal=False):
		raise NotImplementedError

	def parse_response_to_wrong_answer(self, got_literal=False):
		raise NotImplementedError

	def parse_pi(self):
		# parsing a processing instruction in xml, denoted with '<?' literal
		# I couldn't find the '<?' in a few of the simple qti xml examples.
		# Assume not relevant for GIFT.
		raise NotImplementedError

	def parse_prolog(self):
		# not relevant for GIFT documents
		raise NotImplementedError

	def parse_decl(self, got_literal=False):
		# not relevant for XML documents
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
			the name of the element parsed.

		attrs
			a dictionary of attribute values keyed by attribute name.

		emptyFlag
			a boolean; True indicates that the tag was an empty element tag.
		"""
		raise NotImplementedError

	def parse_attribute(self):
		raise NotImplementedError

	def parse_etag(self):
		"""[42] ETag

		For now, assume end tag is always new line '\n'
		"""
		production = "[42] ETag"
		self.parse_required_literal('\n')
		# self.parse_s()
		return

	def parse_content_new(self):
		"""
		::Q1:: 1+1=2 {T}
		
		::Q2:: What's between orange and green in the spectrum?
		{ =yellow # right; good! ~red # wrong, it's yellow ~blue # wrong, it's yellow }

		::Q3:: Two plus {=two =2} equals four.

		::Q4:: Which animal eats which food? { =cat -> cat food =dog -> dog food }

		::Q5:: What is a number from 1 to 5? {#3:2}

		::Q6:: What is a number from 1 to 5? {#1..5}

		::Q7:: When was Ulysses S. Grant born? {#
        =1822:0      # Correct! Full credit.
        =%50%1822:2  # He was born in 1822. Half credit for being close.
		}

		::Q8:: How are you? {}

		The format changes after the question title (after the second set of ::).  Buffer all the text after that,
		and then determine which type it is.
		"""
		while True:
			if isinstance(self.the_char, int):
				self.the_char = chr(self.the_char)
			if self.the_char == '/':
				self.parse_require_literal('//')
				self.parse_comment(True)
			elif self.the_char == ':':
				self.next_char()
				if self.the_char == ':' and not self.in_question:
					self.in_question = True
					self.next_char()
					self.parse_element('questionTitle')
				else:
					self.in_question = False
					self.process_question()
			elif self.the_char == '\n':
				self.next_char()
				return True
			elif self.the_char is None:
				# end of entity
				return True
			else:
				self.parse_char_data()
		return True

	def process_question(self):
		"""
		::Q1:: 1+1=2 {T}
		
		::Q2:: What's between orange and green in the spectrum?
		{ =yellow # right; good! ~red # wrong, it's yellow ~blue # wrong, it's yellow }

		::Q3:: Two plus {=two =2} equals four.
		# Maybe same as QTI inline choice: https://www.imsglobal.org/question/qtiv2p2/examples/items/inline_choice.xml

		::Q4:: Which animal eats which food? { =cat -> cat food =dog -> dog food }

		::Q5:: What is a number from 1 to 5? {#3:2}

		::Q6:: What is a number from 1 to 5? {#1..5}

		::Q7:: When was Ulysses S. Grant born? {#
        =1822:0      # Correct! Full credit.
        =%50%1822:2  # He was born in 1822. Half credit for being close.
		}

		::Q8:: How are you? {}
		"""
		data = []
		in_brackets = False
		after_brackets = False
		qtype = None
		while self.the_char is not None:
			if self.the_char == '{':
				in_brackets = True
				data.append(self.the_char)
				self.next_char()
				if self.the_char == '#':
					if not qtype:
						qtype = 'numeric'
					else:
						raise gift.GIFTFatalError("Parsing error: qtype already assigned, %s" % qtype)
			elif self.the_char == '}':
				in_brackets = False
				after_brackets = True
			elif in_brackets and self.the_char in ('T', 'F'):
				if not qtype:
					qtype = 'truefalse'
				else:
					raise gift.GIFTFatalError("Parsing error: qtype already assigned, %s" % qtype)
			elif after_brackets and self.the_char not in (' ', None):
				if not qtype:
					qtype = 'fillintheblank'
				else:
					raise gift.GIFTFatalError("Parsing error: qtype already assigned, %s" % qtype)
			elif in_brackets and self.the_char == '-':
				data.append(self.the_char)
				self.next_char()
				if self.the_char == '>':
					if not qtype:
						qtype = 'matching'
					else:
						raise gift.GIFTFatalError("Parsing error: qtype already assigned, %s" % qtype)
			data.append(self.the_char)
			self.next_char()

		# if qtype is None, assume it is multiple choice
		for c in data:
			raise NotImplementedError

	digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

	def skip(self):
		while self.the_char in ('\n', ' '):
			self.next_char()
		return not self.the_char

	def parse_content(self):
		while self.the_char is not None:
			if self.the_char == '/':
				self.in_comment = True
				self.parse_required_literal('//')
				self.parse_comment(True)
				# There is always a '\n' after a comment, otherwise the whole line is a comment
			# elif self.in_question:
			# 	# self.parse_required_literal('::')
			# 	self.in_question = False
			# 	self.parse_element('question')
			# elif self.booleanType:
			# 	self.booleanType = False
			# 	self.parse_element('boolean')
			# elif self.in_correct_response:
			# 	self.in_correct_response = False
			# 	self.parse_element('correctResponse')
			# elif self.in_wrong_response:
			# 	self.in_wrong_response = False
			# 	self.parse_element('wrongResponse')
			elif (self.the_char == ':' and not self.in_responses and not self.in_question_title):
				# '::' before question title
				self.in_question_title = True
				self.parse_required_literal('::')
				self.parse_element('questionTitle')
				print("elif (self.the_char == ':' and not self.in_responses and not self.in_question_title)")
			elif (self.the_char == ':' and not self.in_responses and self.in_question_title):
				# '::' before question
				self.in_question = True
				self.in_question_title = False
				self.parse_required_literal('::')
				self.parse_element('question')
				print("elif (self.the_char == ':' and not self.in_responses and self.in_question_title), self.the_char={}".format(self.the_char))
				# return True
			elif (self.the_char == ':' and self.in_responses):
				if self.numericType:
					# this is valid; denotes a range
					self.next_char()
				else:
					raise gift.GIFTValidityError("parse_content(): invalid input, "
						"only expect ':' in responses for numeric_type")
			elif self.the_char == '{':
				# denotes end of question; start of responses
				print("elif self.the_char == '{'")
				self.in_responses = True
				self.in_question = False
				self.firstResponse = True
				self.next_char()
				if self.skip():
					break
				if self.the_char in ('T', 'F'):
					self.booleanType = True
					self.parse_element('boolean')
				elif self.the_char in ('=', '~', '}'):
					# multiple choice, fill-in-the-blank, matching, or essay type
					# do nothing
					print("otherType")
					self.parse_element()
				elif self.the_char == '#':
					print("numericType")
					self.numericType = True
					self.next_char()
					if self.the_char.isdigit():
						# self.in_correct_response = True
						self.parse_element('correctResponse')
				else:
					raise gift.GIFTValidityError("parse_content(): unexpected character "
						"after '{', {}".format(self.the_char))
				print("end of elif self.the_char == '{'")
			elif self.the_char == '=' and self.in_responses:
				self.parse_required_literal('=')
				self.parse_element('correctResponse')
			elif self.the_char == '~' and self.in_responses:
				print("elif self.the_char == '~' and self.in_responses")
				self.parse_required_literal('~')
				self.parse_element('wrongResponse')
				# if self.first_response:
				# 	self.first_response = False
				# 	self.parse_element('wrongResponse')
				# else:
				# 	# self.in_correct_response = False
				# 	self.in_wrong_reponse = True
				# 	return True
			elif self.the_char == '}':
				self.in_responses = False
				self.after_brackets = True
				self.parse_required_literal('}')
				if self.skip():
					break
				if self.the_char.isalnum():
					self.parse_element('aftertheblank')
			elif self.the_char == '\n':
				self.next_char()
				if self.in_comment:
					self.in_comment = False
					self.parse_element()
			else:
				print("before self.parse_char_data(): {}".format(self.the_char))
				self.parse_char_data()
				return True
				print("after self.parse_char_data(): {}".format(self.the_char))
		self.reset()
		return True

	def parse_element(self, name=None):
		print("parse_element({})".format(name))
		save_element = self.element
		save_element_type = self.elementType
		save_cursor = None
		if name:
			context = self.get_context()
			self.element = context.add_child(gift.Element, name)
		self.parse_content()
		# self.element.content_changed()
		self.element = save_element
		self.elementType = save_element_type
		self.cursor = save_cursor
		return True

	def parse_char_data(self):
		"""Parses a run of character data, and adds parsed data to current element.
		"""
		data = []
		while self.the_char is not None:
			if self.in_question and self.the_char in ('{', '\n'):
				print("if self.in_question and self.the_char in ('{', '\n')")
				break
			elif self.numericType and self.the_char in ('{', '\n', '=', '~', '}'):
				break
			elif not (self.in_question or self.numericType) and self.the_char in ('{', '\n', ':', '#', '~', '=', '}'):
				print("elif not self.in_question and self.the_char in ('{', '\n', ':', '#', '~', '=', '}')")
				break
			self.is_s()
			data.append(self.the_char)
			self.next_char()
			if len(data) >= gift.GIFTEntity.chunk_size:
				data = ''.join(data)
				try:
					self.handle_data(data)
				except gift.GIFTValidityError:
					raise
				data = []
		data = ''.join(data)
		print("parse_char_data(): data={}".format(data))
		try:
			self.handle_data(data.strip())
		except gift.GIFTValidityError:
			raise
		return None

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
