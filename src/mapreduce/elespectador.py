import logging

import dumbo

import noticias.parser as noticias_parser
import noticias.noticia_pb2 as noticia_pb2
import scripts.crear_automata
import utils


class NoticiaMapper(object):
    def __call__(self, key, value):
        try:
            noticia = self.parse(value)
        except Exception:
            logging.error('could not parse %s' % key)
        else:
            yield key, noticia

    def parse(self, html):
        html = html.decode('utf-8')
        parser = noticias_parser.ElEspectadorParser(html)
        noticia = parser.as_protobuf_string()
        noticia = parser.as_json()
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
    job.additer(NoticiaMapper, dumbo.lib.identityreducer)
    job.additer(CongresistasMapper, dumbo.lib.identityreducer)
    job.run()
