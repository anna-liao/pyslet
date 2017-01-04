#! /usr/bin/env python

""" Python 3.5 specific methods.

Analogous to pyslet.py2
https://github.com/swl10/pyslet/blob/master/pyslet/py2.py
"""


def character(arg):
	if isinstance(arg, str):
		if len(arg) == 1:
			return chr(ord(arg[0]))
		else:
			raise ValueError('Expected single character')
	else:
		return chr(arg)

join_characters = ''.join
uempty = ''
uspace = ''


def force_bytes(arg):
	if isinstance(arg, str):
		return arg.encode('ascii')
	return arg


def is_byte(arg):
	return isinstance(arg, bytes) and len(arg) == 1

byte_value = ord
join_bytes = b''.join