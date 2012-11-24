import codecs
import hashlib
import heapq

import dumbo
import nltk
import redis

import noticias.parser as noticias_parser
import noticias.noticia_pb2 as noticia_pb2
import scripts.crear_automata
import datastructures.interval_tree


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
    def __call__(self, noticia_id, match_list):
        noticia = self.get_noticia(noticia_id)
        sentence_tree = self.build_sentence_tree(noticia.content)
        matches_heap = self.build_heap(match_list)
        for match in self.no_overlaps_iter(matches_heap):
            if match[2] is not None:
                sentence = sentence_tree.findRange(match[:2])
                assert len(sentence) == 1
                yield sentence[0], match[2]
        
    def build_heap(self, match_list):
        heap = []
        for match in match_list:
            heapq.heappush(heap,
                           (match[0][0], match[0][1], match[1]))
        return heap
    
    def get_noticia(self, noticia_id):
        noticia = noticia_pb2.Article()
        serialized_noticia = r.get('noticia:' + noticia_id)
        noticia.ParseFromString(serialized_noticia)
        return noticia
   
    def build_sentence_tree(self, content):
        sent_detector = nltk.data.load('tokenizers/punkt/spanish.pickle')
        span_list = sent_detector.span_tokenize(content)
        sent_intervals = [(span[0], span[1],
                           content[span[0]:span[1]]) for span in span_list]
        tree = datastructures.interval_tree.IntervalTree(sent_intervals,
                                                        0, 1, 0, len(content))
        return tree
       
    
    def no_overlaps_iter(self, match_list):
        match = heapq.heappop(match_list)
        while True:
            assert(match[0] < match[1])
            if not len(match_list):
                yield match
                break
            next_match = heapq.heappop(match_list)
            if next_match[0] < match[1]:
                if match[2] != next_match[2]:
                    # TODO: Improve NER. This type of errors are currently caused by
                    # duplicate entity matches. 
                    # For now, mark as None and ignore.
                    entity_id = None
                else:
                    entity_id = match[2]
                match = (match[0], max(next_match[1], match[1]), entity_id)
            else:
                if next_match[0] > match[1]:
                    yield match
                match = next_match
        raise StopIteration


class OracionMapper(object):
    def __call__(self, noticia_id, match):
        pass


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(html_mapper, html_reducer)
    job.additer(NoticiaMapper, NoticiaReducer)
    #job.additer(OracionMapper, OracionReducer)
    job.run()
