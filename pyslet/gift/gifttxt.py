


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

	def __init__(self):
		pass

	def read(self, src):
		"""
		Parses a BytesIO object

		Usage: read(src=BytesIO(input))
		input is a b"" string
		"""
		pass