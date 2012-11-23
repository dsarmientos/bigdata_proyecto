import codecs
import hashlib
import heapq

import dumbo
import redis

import noticias.parser as noticias_parser
import noticias.noticia_pb2 as noticia_pb2
import scripts.crear_automata


r = redis.StrictRedis(host='localhost', port=6379, db=0)


def html_mapper(key, value):
    with codecs.open(value, 'r', 'utf-8') as infile:
        html = infile.read()
    yield value, html


def html_reducer(key, value):
    html = value.next()
    yield key, html


class NoticiaMapper(object):
    def __call__(self, key, value):
        try:
            noticia_str = self.parse(value)
        except Exception:
            raise
        else:
            noticia = noticia_pb2.Article()
            noticia.ParseFromString(noticia_str)
            match_list = self.find_congresistas(noticia)
            if match_list:
                noticia_id = self.save_noticia(noticia)
                for match in match_list:
                    yield noticia_id, match

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
    def __call__(self, key, match_list):
        heap = []
        for match in match_list:
            heapq.heappush(heap,
                           (match[0][0], match[0][1], match[1]))
        for match in self.no_overlaps_iter(heap):
            yield key, match 
    
    def no_overlaps_iter(self, match_list):
        match = heapq.heappop(match_list)
        while True:
            assert(match[0] < match[1])
            if not len(match_list):
                yield match
                break
            next_match = heapq.heappop(match_list)
            if next_match[0] < match[1]:
                assert(match[2] == next_match[2])
                match = (match[0], max(next_match[1], match[1]), match[2])
            else:
                if next_match[0] > match[1]:
                    yield match
                match = next_match
        raise StopIteration


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(html_mapper, html_reducer)
    job.additer(NoticiaMapper, NoticiaReducer)
    job.run()
