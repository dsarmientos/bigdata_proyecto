# -*- coding: utf-8 -*-
'''
Created on Nov 19, 2012

@author: daniel
'''
import codecs
import datetime
import parser
import unittest


class Test(unittest.TestCase):

    def setUp(self):
        filename = 'test_data/elespectador.html'
        self.parser = parser.ElEspectadorParser(filename)
        self.encoding = 'utf-8'

    def tearDown(self):
        pass

    def test_get_raw_html(self):
        filename = 'test_data/elespectador_raw_html.txt'
        with codecs.open(filename, 'r', self.encoding) as infile:
            self.expected_raw_html = infile.read()
        self.assertEqual(self.parser.get_raw_html(), self.expected_raw_html)

    def test_get_html(self):
        filename = 'test_data/elespectador_html.txt'
        with codecs.open(filename, 'r', self.encoding) as infile:
            self.expected_html = infile.read()
        self.assertEqual(self.parser.get_html(), self.expected_html)

    def test_extract_content(self):
        filename = 'test_data/elespectador_content.txt'
        with codecs.open(filename, 'r', self.encoding) as infile:
            self.expected_content = infile.read().rstrip('\n')
        self.assertEqual(self.parser.extract_content(), self.expected_content)

    def test_extract_title(self):
        self.expected_title = (
            u'Gobierno insiste en que no quiere propiciar '
            u'impunidad en juzgamiento de militares')
        self.assertEqual(self.parser.extract_title(), self.expected_title)

    def test_extract_section(self):
        self.expected_section = u'Política'
        self.assertEqual(self.parser.extract_section(), self.expected_section)

    def test_extract_date(self):
        self.expected_date = datetime.datetime(2012, 01, 13, 10, 44)
        self.assertEqual(self.parser.extract_date(), self.expected_date)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
