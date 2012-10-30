import re

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


def extract_filename(url):
    title_re = re.compile(
        r'(?:http://)?www\.semana\.com/+(?:politica|nacion)/([-\w]+)/.+\.aspx/?$'
    )
    match = title_re.match(url)
    if match:
        return match.groups()[0]


class SemanaSpider(CrawlSpider):
    name = "semana"
    allowed_domains = ["www.semana.com"]
    start_urls = [
            'http://www.semana.com/politica/online/164-2.aspx',
            'http://www.semana.com/wf_Buscador.aspx?Buscar=politica',
            'http://www.semana.com',
            'http://www.semana.com/nacion/online/3-2.aspx',
            'http://www.semana.com/wf_Buscador.aspx?Buscar=congreso',
            'http://www.semana.com/wf_Buscador.aspx?Buscar=senado',
            'http://www.semana.com/wf_Buscador.aspx?Buscar=congresista',
            'http://www.semana.com/wf_Buscador.aspx?Buscar=representante',
    ]
    rules = (
        # Parse this pages
        Rule(
            SgmlLinkExtractor(allow=(r'www\.semana\.com//?(politica|nacion)/[-\w]+/.+\.aspx$')),
            callback='parse_page',
            follow=True),
        # Follow this links
        Rule(
            SgmlLinkExtractor(allow=(r'www\.semana\.com/.*',),
                              deny=(r'www\.semana\.com/documents/.+$',
                                    r'www\.semana\.com/wf_.*')),
            follow=True),
    )

    def parse_page(self, response):
        if hasattr(response, 'url'):
            filename = extract_filename(response.url)
            if filename:
                with open(filename, 'wb') as outf:
                    outf.write(response.body)
