import re

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


def extract_filename(url):
    title_re = re.compile(
        r'(?:http://)?www\.elespectador\.com/noticias/'
        r'(?:politica|nacional)/[-\w]+articulo-([-\w]+)/?$'
    )
    match = title_re.match(url)
    if match:
        return match.groups()[0]


class ElEspectadorSpider(CrawlSpider):
    name = "elespectador"
    allowed_domains = ["www.elespectador.com"]
    start_urls = [
        'http://www.elespectador.com',
        'http://www.elespectador.com/noticias/politica/',
        'http://www.elespectador.com/noticias/nacional/',
    ]
    rules = (
        # Parse this pages
        Rule(
            SgmlLinkExtractor(
                allow=(
                    r'www.elespectador.com/noticias/'
                    r'(?:politica|nacional)/[-\w]+articulo-[-\w]+/?$')),
            callback='parse_page',
            follow=True),
        # Follow this links
        Rule(
            SgmlLinkExtractor(allow=(r'www.elespectador.com/\.*',)),
            follow=True),
    )

    def parse_page(self, response):
        filename = extract_filename(response.url)
        with open(filename, 'wb') as outf:
            outf.write(response.body)
