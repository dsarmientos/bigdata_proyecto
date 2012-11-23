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
            match_list = self.find_congresistas(noticia)
            for match in match_list:
                i = match[0]
                yield key, '%s:%s' % (noticia.content[i[0]:i[1]], match[1])

    def parse(self, html):
        html = html.decode('utf-8')
        parser = noticias_parser.ElEspectadorParser(html)
        noticia = parser.as_protobuf_string()
        return noticia

    def find_congresistas(self, noticia_str):
        noticia = noticia_pb2.Article()
        noticia.ParseFromString(noticia_str)
        automata = scripts.crear_automata.get_automata()
        content = noticia.content
        return automata.query(content)


class NoticiaReducer(object):
    def __call__(self, key, values):
        yield key, ' '.join(values)


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(NoticiaMapper, NoticiaReducer)
    job.run()
