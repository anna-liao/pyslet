from unittests.test_gift_parser import *

# s = """::Q1::1+1=2{T}"""
# s = """//comment\n::Question title::Question{=A correct answer ~Wrong answer1}"""
s = """//comment\n::Question title\n::Question{\n=A correct answer\n~Wrong answer1\n~Wrong answer2\n~Wrong answer3\n}"""
e = structures.GIFTEntity(s)
p = parser.GIFTParser(e)
element = p.element = structures.Element("a")
p.parse_element()
children = list(element.get_children())

print("Length of children: {}".format(len(children)))
for child in children:
	if isinstance(child, structures.Element):
		print("{}, {}".format(child.giftname, child.get_value()))
	else:
		print("WARNING, child is string type: {}".format(child))