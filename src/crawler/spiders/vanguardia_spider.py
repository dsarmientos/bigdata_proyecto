import re

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


def extract_filename(url):
    title_re = re.compile(
        r'(?:http://)?www\.vanguardia\.com/actualidad/(?:politica|colombia)/[-0-9]*([-\w]+)/?$',
    )
    match = title_re.match(url)
    if match:
        return match.groups()[0]


class VanguardiaSpider(CrawlSpider):
    name = "vanguardia"
    allowed_domains = ["www.vanguardia.com"]
    start_urls = [
        'http://www.vanguardia.com',
        'http://www.vanguardia.com/actualidad/politica/',
        'http://www.vanguardia.com/search/apachesolr_search/senador?filters=type%3Anoticia%20tid%3A3027',
        'http://www.vanguardia.com/search/apachesolr_search/congreso',
    ]
    rules = (
        # Parse this pages
        Rule(
            SgmlLinkExtractor(
                allow=(
                    r'www\.vanguardia\.com/actualidad/(politica|colombia)/[-\w]+/?$',)
                    #deny=(r'.*CMS[-].*', r'.*\.(?:pdf|PDF)', r'.*MAM[-].*'),
            ),
            callback='parse_page',
            follow=True),
        # Follow this links
        Rule(
            SgmlLinkExtractor(
                allow=(r'www\.vanguardia\.com/.*'),
                deny=(r'.*\.(pdf|PDF)',)
            ),
            follow=True),
    )

    def parse_page(self, response):
        filename = extract_filename(response.url)
        with open(filename, 'wb') as outf:
            outf.write(response.body)
