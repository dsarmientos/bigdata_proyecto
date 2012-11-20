'''
Created on Nov 19, 2012

@author: Daniel Sarmiento
'''

import datetime
import codecs
import htmlentitydefs
import lxml.html
import re
import xml.sax.saxutils


class BaseParser(object):
    def __init__(self, filename, encoding='utf-8'):
        self.filename = filename
        self.encoding = encoding
        self.doc = None

    def get_raw_html(self):
        html = ''
        with codecs.open(self.filename, 'r', self.encoding) as infile:
            html = infile.read()
        return html

    def get_html(self):
        entity2unicode = {}
        for name, point in htmlentitydefs.name2codepoint.items():
            entity2unicode['&%s;' % name] = unichr(point)
        unicode_html = xml.sax.saxutils.unescape(self.get_raw_html(),
                                                 entity2unicode)
        return unicode_html.strip()

    def get_html_doc(self):
        if self.doc is None:
            self.doc = lxml.html.fromstring(self.get_html())
        return self.doc

    def as_json(self):
        raise NotImplementedError('as_json() must be implemented in subclass')


class ElEspectadorParser(BaseParser):
    def as_json(self):
        pass

    def extract_content(self):
        doc = self.get_html_doc()
        content_div = doc.xpath('//div[@class="content_nota"]')[0]
        p_list = content_div.findall('p')
        ws_re = re.compile('\s\s+')
        content_ = lambda p: p.text_content().strip()
        p_text_list = [ws_re.sub(' ', content_(p)) for p in p_list]
        content = unicode('\n\n'.join(p_text_list))
        return content

    def extract_title(self):
        doc = self.get_html_doc()
        h1 = doc.xpath('//div[@class="header_nota"]/h1')[0]
        title = unicode(h1.text.strip())
        return title

    def extract_section(self):
        doc = self.get_html_doc()
        h4 = doc.xpath('//div[@class="header_nota"]/h4')[0]
        seccion_a = h4.find_class('seccion')[0]
        seccion = unicode(seccion_a.text.strip())
        return seccion

    def extract_date(self):
        doc = self.get_html_doc()
        datetime_re = re.compile(
            r'([0-9]{2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)'
            r'\s+([0-9]{4})\s+[-]\s+([0-9]{2}):([0-9]{2})\s+(am|pm)',
            re.I)
        h4 = doc.xpath('//div[@class="header_nota"]/h4')[0]
        match = datetime_re.search(h4.text_content())
        if match:
            month_name2num = dict(zip(
                ('ene', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'ago',
                 'sep', 'oct', 'nov', 'dic'),
                range(1, 13)))
            day, month_name, year, hour, minute, am_pm = match.groups()
            month = month_name2num[month_name.lower()]
            year, day, hour, minute = (int(year), int(day), int(hour),
                                       int(minute))
            if am_pm.lower() == 'pm':
                hour = (hour + 12) % 24
            return datetime.datetime(year, month, day,
                                     hour, minute)
