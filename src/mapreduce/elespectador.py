import hashlib
import logging

import dumbo
import redis

import noticias.parser as noticias_parser
import noticias.noticia_pb2 as noticia_pb2
import scripts.crear_automata


r = redis.StrictRedis(host='bigdata-12-a', port=6379, db=0)


class NoticiaMapper(object):
    def __call__(self, filename, html):
        try:
            html = html.decode('utf-8')
            noticia_str = self.parse(html)
        except Exception:
            logging.info('could not parse file "%s"' % filename)
        else:
            noticia = noticia_pb2.Article()
            noticia.ParseFromString(noticia_str)
            match_list = self.find_congresistas(noticia)
            if match_list:
                noticia_id = self.save_noticia(noticia)
                for match in match_list:
                    i = match[0]
                    yield noticia_id, '%s:%s' % (noticia.content[i[0]:i[1]],
                                                 match[1])

    def parse(self, html):
        parser = noticias_parser.ElEspectadorParser(html)
        noticia = parser.as_protobuf_string()
        return noticia

    def find_congresistas(self, noticia):
        automata = scripts.crear_automata.get_automata()
        content = noticia.content
        return automata.query(content)

    def save_noticia(self, noticia):
        id_ = hashlib.sha1(noticia.content).hexdigest()
        r.setnx('noticia:' + id_, noticia.SerializeToString())
        return id_


class NoticiaReducer(object):
    def __call__(self, key, values):
        yield key, ' '.join(values)


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(NoticiaMapper, NoticiaReducer)
    job.run()
