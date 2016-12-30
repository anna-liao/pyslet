
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

from .structures import (
	Document
	)

from . import (
	content,
	processing,
	interactions,
	variables
	)



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

	"""

	if not isinstance(scope, dict):
		scope = scope.__dict__
	for name in dict_keys(scope):
		obj = scope[name]
