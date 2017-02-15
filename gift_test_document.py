from unittests.test_gift_parser import *

os.chdir(TEST_DATA_DIR)
with open('readFile.txt', 'rb') as f:
	with structures.GIFTEntity(f) as e:
		d = structures.Document()
		d.read(e)