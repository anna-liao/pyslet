from unittests.test_gift_parser import *

s = """//comment\n::Question title::Question{=A correct answer ~Wrong answer1}"""
# s = """//comment\n::Question title\n::Question{\n=A correct answer\n~Wrong answer1\n~Wrong answer2\n~Wrong answer3\n}"""
# s = """::Q1::1+1=2{T}"""
# s = """::Q2:: What's between orange and green in the spectrum?
# { =yellow # right; good! ~red # wrong, it's yellow ~blue # wrong, it's yellow }
# """
# s = """::Q3:: Two plus {=two =2} equals four."""
# s = """::Q4:: Which animal eats which food? { =cat -> cat food =dog -> dog food }"""
# s = """::Q5:: What is a number from 1 to 5? {#3:2}"""
# s = """::Q6:: What is a number from 1 to 5? {#1..5}"""
# s = """::Q7:: When was Ulysses S. Grant born? {#
#          =1822:0      # Correct! Full credit.
#          =%50%1822:2  # He was born in 1822. Half credit for being close.
# }"""

e = structures.GIFTEntity(s)
p = parser.GIFTParser(e)
element = p.element = structures.Element("a")
p.parse_element()
children = list(element.get_children())

print("Length of children: {}".format(len(children)))
for child in children:
	if isinstance(child, structures.Element):
		print("{}, '{}'".format(child.giftname, child.get_value()))
	else:
		print("WARNING, child is string type: {}".format(child))