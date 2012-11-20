'''
Created on Nov 19, 2012

@author: Daniel Sarmiento
'''

import pdb
import datetime
import htmlentitydefs
import re
import xml.sax.saxutils

import lxml.html
import simplejson


class BaseParser(object):
    def __init__(self, html, encoding):
        self.raw_html = html
        self.encoding = encoding
        self.doc = None

    def get_html(self):
        entity2unicode = {}
        for name, point in htmlentitydefs.name2codepoint.items():
            entity2unicode['&%s;' % name] = unichr(point)
        unicode_html = xml.sax.saxutils.unescape(self.raw_html,
                                                 entity2unicode)
        return unicode_html.strip()

    def get_html_doc(self):
        if self.doc is None:
            self.doc = lxml.html.fromstring(self.get_html())
        return self.doc

    def as_json(self):
        raise NotImplementedError('as_json() must be implemented in subclass')


class ElEspectadorParser(BaseParser):
    def __init__(self, html, encoding='utf-8'):
        super(ElEspectadorParser, self).__init__(html, encoding)
    
    def as_json(self):
        date = self.extract_date().isoformat()
        noticia = {
            'media': 'elespectador',
            'date': date,
            'section': self.extract_section(),
            'title': self.extract_title(),
            'content': self.extract_content(),
        }
        return simplejson.dumps(noticia)
        

    def extract_content(self):
        doc = self.get_html_doc()
        content_div = doc.xpath('//div[@class="content_nota"]')[0]
        p_list = content_div.findall('p')
        if not p_list:
            p_list = content_div.findall('div')
        ws_re = re.compile('\s\s+')
        content_ = lambda p: p.text_content().strip()
        p_text_list = [ws_re.sub(' ', content_(p)) for p in p_list]
        content = unicode('\n\n'.join(p_text_list))
        return content.strip()

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
            r'([0-9]{1,2})\s+'
            r'(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[a-z]*'
            r'\s+([0-9]{4})\s+[-]\s+([0-9]{1,2}):([0-9]{1,2})\s+(am|pm)',
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
