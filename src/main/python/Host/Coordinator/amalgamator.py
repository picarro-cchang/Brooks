import unittest

str1 = "This is a test\n"
str2 = "This is a test\nThis is the second line\n"
str3 = "This is a test\nThis is the second line\nThis is the third line\n"
str4 = "This is a completely new\n"
str5 = "This is a completely new\nAnd a new line after\n"

class Amalgamator(object):
    def __init__(self):
        self.result = ""
        self.pos = 0
    def addText(self,text):
        if text.startswith(self.result[self.pos:]):
            self.result = self.result[:self.pos] + text
        else:
            self.pos = len(self.result)
            self.result += text

class TestAmalgamator(unittest.TestCase):
    def setUp(self):
        self.amalgamator = Amalgamator()
        pass
    def tearDown(self):
        pass
    def testBasic(self):
        self.amalgamator.addText(str1)
        self.assertEqual(self.amalgamator.result,str1)
    def testJoin(self):
        self.amalgamator.addText(str1)
        self.amalgamator.addText(str2)
        self.assertEqual(self.amalgamator.result,str2)
        self.amalgamator.addText(str3)
        self.assertEqual(self.amalgamator.result,str3)
    def testAddNew(self):
        self.amalgamator.addText(str1)
        self.amalgamator.addText(str2)
        self.amalgamator.addText(str3)
        self.amalgamator.addText(str4)
        self.assertEqual(self.amalgamator.result,str3+str4)
        self.amalgamator.addText(str5)
        self.assertEqual(self.amalgamator.result,str3+str5)
    def testAnotherChange(self):
        self.amalgamator.addText(str1)
        self.amalgamator.addText(str2)
        self.amalgamator.addText(str3)
        self.amalgamator.addText(str4)
        self.amalgamator.addText(str5)
        self.amalgamator.addText(str1)
        self.assertEqual(self.amalgamator.result,str3+str5+str1)
        self.amalgamator.addText(str1)
        self.assertEqual(self.amalgamator.result,str3+str5+str1)
        self.amalgamator.addText(str3)
        self.assertEqual(self.amalgamator.result,str3+str5+str3)

if __name__ == "__main__":
    unittest.main()