'''
Created on Nov 19, 2012

@author: Daniel Sarmiento
'''

import datetime
import htmlentitydefs
import re
import xml.sax.saxutils

import lxml.html
import simplejson

import noticia_pb2
import utils


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


    def as_protobuf_string(self):
        date = self.extract_date().isoformat()
        noticia = noticia_pb2.Article()
        noticia.media = 'elespectador'
        noticia.date = date
        noticia.section = self.extract_section()
        noticia.title = self.extract_title()
        noticia.content = self.extract_content()
        return noticia.SerializeToString()


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
        return utils.remove_accents(content.strip())

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
                ('ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago',
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


class ElTiempoParser(BaseParser):
    def __init__(self, html, encoding='latin-1'):
        super(ElTiempoParser, self).__init__(html, encoding)

    def as_json(self):
        date = self.extract_date().isoformat()
        noticia = {
            'media': 'eltiempo',
            'date': date,
            'section': self.extract_section(),
            'title': self.extract_title(),
            'content': self.extract_content(),
        }
        return simplejson.dumps(noticia)


    def as_protobuf_string(self):
        date = self.extract_date().isoformat()
        noticia = noticia_pb2.Article()
        noticia.media = 'eltiempo'
        noticia.date = date
        noticia.section = self.extract_section()
        noticia.title = self.extract_title()
        noticia.content = self.extract_content()
        return noticia.SerializeToString()


    def extract_content(self):
        doc = self.get_html_doc()
        content_div = doc.xpath('//div[@class="despliegue-txt"]')[0]
        p_list = content_div.findall('p')
        if not p_list:
            p_list = content_div.findall('div')
        ws_re = re.compile('\s\s+')
        content_ = lambda p: p.text_content().strip()
        p_text_list = [ws_re.sub(' ', content_(p)) for p in p_list]
        content = unicode('\n\n'.join(p_text_list))
        return utils.remove_accents(content.strip())

    def extract_title(self):
        doc = self.get_html_doc()
        h1 = doc.xpath('//div[@id="contenidoArt"]/h1')[0]
        title = unicode(h1.text.strip())
        return title

    def extract_section(self):
        doc = self.get_html_doc()
        p = doc.xpath('//p[@class="creditos"]')[0]
        por = p.text_content().strip().split('|')[0]
        seccion = por.strip()[4:].strip().title()
        return seccion

    def extract_date(self):
        doc = self.get_html_doc()
        p = doc.xpath('//p[@class="creditos"]')[0]
        creditos = p.text_content().strip().split('|')
        hora, fecha = creditos[1].strip(), creditos[2].strip()
        
        hora_re = re.compile(
            r'([0-9]{1,2}):([0-9]{1,2})\s+(a\.?m\.?|p\.?m\.?)',
            re.I)
        match = hora_re.search(hora)
        hour, minute, am_pm = match.groups()
        datetime_re = re.compile(
            r'([0-9]{1,2})\s*de\s*'
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|'
            r'octubre|noviembre|diciembre)[a-z]*'
            r'\s+del\s*([0-9]{4})',
            re.I)
        match = datetime_re.search(fecha)
        if match:
            month_name2num = dict(zip(
                ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
                 'septiembre', 'octubre', 'noviembre', 'diciembre'),
                range(1, 13)))
            day, month_name, year = match.groups()
            month = month_name2num[month_name.lower()]
            year, day, hour, minute = (int(year), int(day), int(hour),
                                       int(minute))
            if am_pm.lower() == 'pm':
                hour = (hour + 12) % 24
            return datetime.datetime(year, month, day,
                                     hour, minute)
