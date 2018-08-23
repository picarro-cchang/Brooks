"""Unittest version of minimock tests"""

from unittest import main, TestCase
from Host.Doctests.MiniMock.testExample import send_email, get_open_file, MyClass
import doctest
import minimock
import smtplib

tt = minimock.TraceTracker()
tt.options &= ~doctest.REPORT_UDIFF

def Mock(*a,**k):
    k.update(dict(tracker=tt))
    return minimock.Mock(*a,**k)

def mock(*a,**k):
    k.update(dict(tracker=tt))
    return minimock.mock(*a,**k)

def assert_same_trace(want):
    try:
        minimock.assert_same_trace(tt,want)
    finally:
        tt.clear()

class FirstTestCase(TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test1(self):
        """Example of mocking smtp.SMTP object"""
        smtplib.SMTP = Mock('smtplib.SMTP')
        smtplib.SMTP.mock_returns = Mock('smtp_connection')
        send_email('ianb@colorstudy.com','joe@example.com','Hi there!',
                   'How is it going?')
        assert_same_trace("""\
        Called smtplib.SMTP('localhost')
        Called smtp_connection.sendmail(
            'ianb@colorstudy.com',
            ['joe@example.com'],
            'To: joe@example.com\\nFrom: ianb@colorstudy.com\\nSubject: Hi there!\\n\\nHow is it going?')
        Called smtp_connection.quit()
        """)
    def test2(self):
        """Example of mocking built-in open function and file_handle class"""
        mock('open',returns = Mock('file_handle'))
        fp = get_open_file('/test/test/test')
        assert_same_trace("""Called open('/test/test/test', 'w')""")
        fp.write("This writes to the file")
        assert_same_trace("""Called file_handle.write('This writes to the file')""")
    def test3(self):
        """The class MyClass defines method3 to be the sum of method2 and method1.
        Both method1 and method2 are somewhat complex, so we mock them to test
        method3 by itself"""
        m = MyClass()
        m.method1 = Mock('MyClass.method1')
        m.method1.mock_returns = 5
        m.method2 = Mock('MyClass.method2')
        m.method2.mock_returns = 7
        """Now we invoke method3, which calls our mock methods and finds their sum.
        Notice that the argument to Mock gives the string printed out when the
        mock object is called"""
        self.assertEqual(m.method3(42),12)
        assert_same_trace("""\
        Called MyClass.method1(42)
        Called MyClass.method2(42)
        """)
    def test4(self):
        """Alternatively, we can mock the methods within the class beforehand, so
        that the object p gets the mocked methods"""
        mock('MyClass.method1',returns=8)
        mock('MyClass.method2',returns=9)
        p = MyClass()
        self.assertEqual(p.method3(65),17)
        assert_same_trace("""\
        Called MyClass.method1(65)
        Called MyClass.method2(65)
        """)
        """Using restore reverts MyClass to its original state"""
        minimock.restore()
        p = MyClass()
        self.assertAlmostEqual(p.method3(42),130.83597245795309)
    def test5(self):
        """method4 in MyClass uses the id function on self, and calls method3 with
        the result. In the following, we mock id so that it returns a known
        value and also mock method3 so that we can see that the value is
        correctly passed."""
        mock('id',returns=123)
        mock('MyClass.method3')
        p = MyClass()
        p.method4()
        assert_same_trace("""\
        Called id(<...MyClass object ...>)
        Called MyClass.method3(123)
        """)

if __name__ == "__main__":
    main()