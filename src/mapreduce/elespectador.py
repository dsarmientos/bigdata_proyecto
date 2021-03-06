import codecs
import collections
import hashlib
import heapq
import string

import dumbo
import nltk
import redis

import noticias.parser as noticias_parser
import noticias.noticia_pb2 as noticia_pb2
import scripts.crear_automata
import datastructures.interval_tree
import utils


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
        sentence_match = {}
        for match in self.no_overlaps_iter(matches_heap):
            person_id, match_range = match[2], match[:2]
            if person_id is not None:
                sentences = sentence_tree.findRange(match_range)
                assert len(sentences) == 1
                sentence = sentences[0]
                sentence_id = hashlib.sha1(sentence).hexdigest()[:10]
                if sentence_id not in sentence_match:
                    sentence_match[sentence_id] = {'sentence': sentence,
                                                   'people_ids': set((person_id,))}
                else:
                    sentence_match[sentence_id]['people_ids'].add(person_id)
        for sentence_id, match in sentence_match.iteritems():
            yield sentence_id, (match['sentence'],
                                list(match['people_ids']))
        
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
    def __call__(self, sentence_id, sentence_people_list):
        self.sentence = sentence_people_list[0].rstrip('.').lower()
        people_list = self.get_people_list(
            sentence_people_list[1])
        self.pipe = r.pipeline()
        self.index_sentence(people_list)
        self.pipe.sadd('indexados:oraciones', sentence_id)
        self.pipe.execute()
        yield self.sentence, people_list

    def get_people_list(self, id_list):
        pipe = r.pipeline()
        for id_ in id_list:
            pipe.hget('congresista:' + str(id_),
                      'nombre_ascii')
        names = pipe.execute()
        return zip(id_list, names)
            
        
    def index_sentence(self, people_list):
        stop_words = self.load_stop_words()
        terms_tf = self.get_terms_tf(stop_words)
        for person_id, person_name in people_list:
            self.add_terms_to(terms_tf, person_id, person_name)
            self.pipe.sadd('indexados:congresistas', person_id)
            
    def load_stop_words(self):
        stop_words = [
            utils.remove_accents(w.decode('utf-8'))
            for w in nltk.corpus.stopwords.words(
                'spanish')]
        return stop_words

    def add_terms_to(self, terms_tf, person_id, person_name):
        congresista_id = str(person_id)
        palabras_nombre = [p.lower() for p in person_name.split(' ')]
        for term, tf in terms_tf.iteritems():
            if term not in palabras_nombre:
                self.pipe.zincrby('indice:congresista:' + str(congresista_id),
                                  term, tf)

    def get_terms_tf(self, stopwords):
        tokenizer = nltk.RegexpTokenizer('\s+', gaps=True)
        trans_table = dict(
            (ord(symbol), u'') for symbol in string.punctuation)
        terms_tf = collections.defaultdict(float)
        for token in tokenizer.tokenize(self.sentence):
            token = token.translate(trans_table).strip()
            if token not in stopwords and len(token) > 1:
                terms_tf[token] += 1
        return terms_tf
            
        


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(html_mapper, html_reducer)
    job.additer(NoticiaMapper, NoticiaReducer)
    job.additer(OracionMapper, dumbo.lib.identityreducer)
    job.run()
