import codecs

import dumbo
import simplejson

import noticias.parser as noticias_parser


def html_mapper(key, value):
    with codecs.open(value, 'r', 'utf-8') as infile:
        html = infile.read()
    yield value, html


def reducer(key, value):
    html = value.next()
    yield key, html


class NoticiaMapper(object):
    def __call__(self, key, value):
        noticia = self.parse(value)
        yield key, noticia

    def parse(self, html):
        parser = noticias_parser.ElEspectadorParser(html)
        noticia = parser.as_json()
        return simplejson.dumps(noticia)


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(html_mapper, reducer)
    job.additer(NoticiaMapper, reducer)
    job.run()