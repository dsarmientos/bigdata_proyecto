import codecs

import dumbo
import simplejson

import noticias.parser as noticias_parser
import noticias.noticia_pb2 as noticia_pb2
import scripts.crear_automata
import utils


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
        noticia = parser.as_protobuf_string()
        return noticia

class CongresistasMapper(object):
    def __call__(self, key, value):
        congresistas = self.find_congresistas(value)
        yield key, congresistas

    def find_congresistas(self, noticia_str):
        noticia = noticia_pb2.Article()
        noticia.ParseFromString(noticia_str)
        content = utils.remove_accents(noticia.content)
        automata = scripts.crear_automata.get_automata()
        congresistas = []
        for i in automata.findall(content):
            congresistas.append(content[i[0]:i[1]])
        return congresistas 


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(html_mapper, reducer)
    job.additer(NoticiaMapper, dumbo.lib.identityreducer)
    job.additer(CongresistasMapper, dumbo.lib.identityreducer)
    job.run()