# Scrapy settings for tutorial project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'crawler'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'
USER_AGENT = '%s/%s' % ('Mozilla', '5.001')

SPIDER_MIDDLEWARES = [
    'scrapy.contrib.spidermiddleware.offsite.OffsiteMiddleware',
]
