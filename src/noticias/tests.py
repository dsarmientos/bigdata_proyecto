# -*- coding: utf-8 -*-
'''
Created on Nov 19, 2012

@author: daniel
'''
import codecs
import datetime
import parser
import unittest

import simplejson

import noticia_pb2

class Test(unittest.TestCase):

    def setUp(self):
        html_file = 'test_data/elespectador.html'
        with codecs.open(html_file, 'r', 'utf-8') as infile:
            html = infile.read()
        self.parser = parser.ElEspectadorParser(html)
        self.encoding = 'utf-8'
        self.expected_date = datetime.datetime(2012, 01, 13, 10, 44)
        self.expected_section = u'Política'
        self.expected_title = (
            u'Gobierno insiste en que no quiere propiciar '
            u'impunidad en juzgamiento de militares')
        content_file = 'test_data/elespectador_content.txt'
        with codecs.open(content_file, 'r', self.encoding) as infile:
            self.expected_content = infile.read().rstrip('\n')

    def tearDown(self):
        pass

    def test_raw_html(self):
        filename = 'test_data/elespectador_raw_html.txt'
        with codecs.open(filename, 'r', self.encoding) as infile:
            self.expected_raw_html = infile.read()
        self.assertEqual(self.parser.raw_html, self.expected_raw_html)

    def test_get_html(self):
        filename = 'test_data/elespectador_html.txt'
        with codecs.open(filename, 'r', self.encoding) as infile:
            self.expected_html = infile.read()
        self.assertEqual(self.parser.get_html(), self.expected_html)

    def test_extract_content(self):
        self.assertEqual(self.parser.extract_content(), self.expected_content)

    def test_extract_title(self):
        self.assertEqual(self.parser.extract_title(), self.expected_title)

    def test_extract_section(self):
        self.assertEqual(self.parser.extract_section(), self.expected_section)

    def test_extract_date(self):
        self.assertEqual(self.parser.extract_date(), self.expected_date)
    
    def test_as_json(self):
        noticia = simplejson.loads(self.parser.as_json())
        date = self.expected_date.isoformat()
        fields = ('media', 'date', 'title', 'content', 'section')
        expected_noticia = dict(
            zip(fields,
                ('elespectador', date, self.expected_title,
                self.expected_content, self.expected_section))
        )
        for field in fields:
            self.assertTrue(field in noticia,
                            'Falta campo olbigatorio "%s" en noticia' % field)
        for field, value in noticia.items():
            self.assertEqual(value, expected_noticia[field])

    def test_as_protobuf_string(self):
        noticia = noticia_pb2.Article()
        noticia.ParseFromString(self.parser.as_protobuf_string())
        date = self.expected_date.isoformat()
        fields = ('media', 'date', 'title', 'content', 'section')
        expected_noticia = dict(
            zip(fields,
                ('elespectador', date, self.expected_title,
                self.expected_content, self.expected_section))
        )
        self.assertEqual(noticia.content, expected_noticia['content'])

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
