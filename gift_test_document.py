from unittests.test_gift_parser import *

os.chdir(TEST_DATA_DIR)

with open('readFile.txt', 'rb') as f:
	with structures.GIFTEntity(f) as e:
		p = parser.GIFTParser(e)
		p.parse_document()
root = p.doc.root

# d = structures.Document(base_uri='readFile.txt')
# d.read()
# with open('readFile.txt', 'rb') as f:
# 	flines = f.read().splitlines()
# dlines = bytes(d).split(b'\n')

# children = list(d.get_children())
# print("Length of children: {}".format(len(children)))
# for child in children:
# 	if isinstance(child, structures.Element):
# 		print("{}, '{}'".format(child.giftname, child.get_value()))
# 	else:
# 		print("WARNING, child is string type: {}".format(child))

# with open('readFile.txt', 'rb') as f:
# 	d.read(src=f)
# root = d.root