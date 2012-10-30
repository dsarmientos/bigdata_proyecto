import re

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


def extract_filename(url):
    title_re = re.compile(
        r'(?:http://)?www\.eltiempo\.com/(?:politica|justicia)/([-\w]+)/?$'
    )
    match = title_re.match(url)
    if match:
        return match.groups()[0]


class ElEspectadorSpider(CrawlSpider):
    name = "eltiempo"
    allowed_domains = ["www.eltiempo.com"]
    start_urls = [
        'http://www.eltiempo.com',
        'http://www.eltiempo.com/politica/',
        'http://www.eltiempo.com/justicia/',
    ]
    rules = (
        # Parse this pages
        Rule(
            SgmlLinkExtractor(
                allow=(
                    r'www\.eltiempo\.com/(?:politica|justicia)/[-\w]+/?$',),
                deny=(r'.*CMS[-].*', r'.*\.(?:pdf|PDF)', r'.*MAM[-].*'),
            ),
            callback='parse_page',
            follow=True),
        # Follow this links
        Rule(
            SgmlLinkExtractor(
                allow=(r'www\.eltiempo\.com/.*'),
                deny=(r'.*CMS[-].*', r'.*\.(?:pdf|PDF)', r'.*MAM[-].*'),
            ),
            follow=True),
    )

    def parse_page(self, response):
        filename = extract_filename(response.url)
        with open(filename, 'wb') as outf:
            outf.write(response.body)
