from unittests.test_gift_parser import *

os.chdir(TEST_DATA_DIR)

d = structures.Document(base_uri='readFile.txt')
d.read()
with open('readFile.txt', 'rb') as f:
	flines = f.read().splitlines()
dlines = bytes(d)

children = list(d.get_children())
print("Length of children: {}".format(len(children)))
for child in children:
	if isinstance(child, structures.Element):
		print("{}, '{}'".format(child.giftname, child.get_value()))
	else:
		print("WARNING, child is string type: {}".format(child))

	# d.read(src=f)
	# with structures.GIFTEntity(f) as e:
	# 	p = parser.GIFTParser(e)
	# 	# p.element = structures.Element("a")
	# 	p.parse_document()
	# 	root = p.doc.root
	# with structures.GIFTEntity(f) as e:
	# 	d = structures.Document()
	# 	d.read(e)

# document object requires DTD