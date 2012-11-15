import re

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


def extract_filename(url):
    title_re = re.compile(
        r'(?:http://)?www\.elpais\.com\.co/elpais/(?:judicial|colombia)/noticias/([-\w]+)/?$',
    )
    match = title_re.match(url)
    if match:
        return match.groups()[0]


class ElpaisSpider(CrawlSpider):
    name = "elpais"
    allowed_domains = ["www.elpais.com.co"]
    start_urls = [
        'http://www.elpais.com.co',
        'http://www.elpais.com.co/elpais/colombia',
        'http://www.elpais.com.co/elpais/judicial',
    ]
    rules = (
        # Parse this pages
        Rule(
            SgmlLinkExtractor(
                allow=(
                    r'^(?:http://)?www\.elpais\.com\.co/elpais/(judicial|colombia)/noticias/[-\w]+/?$',)
            ),
            callback='parse_page',
            follow=True),
        # Follow this links
        Rule(
            SgmlLinkExtractor(
                allow=(r'^(?:http://)?www\.elpais\.com\.co/[-\w]+/noticias/.*'),
                deny=(r'.*\.(pdf|PDF)',)
            ),
            follow=True),
    )

    def parse_page(self, response):
        filename = extract_filename(response.url)
        with open(filename, 'wb') as outf:
            outf.write(response.body)
