import codecs
import collections
import hashlib
import heapq
import string
import sys
import traceback

import dumbo
import nltk
import redis

import noticias.parser as noticias_parser
import noticias.noticia_pb2 as noticia_pb2
import scripts.crear_automata
import datastructures.interval_tree
import utils


r = redis.StrictRedis(host='bigdata-12-a', port=6379, db=0)


class NoticiaMapper(object):
    def __call__(self, filename, html):
        try:
            html = html.decode('utf-8')
            noticia_str = self.parse(html)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value,
                                               exc_traceback)
            # Let's hope redis is not causing the exception :)
            r.sadd('errores:hadoop',
                   "Could not parse:'%s'. [%s]" % (filename, ''.join(lines)))
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
        self.key = noticia_id
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
                    r.sadd('errores:hadoop',
                           'match %s - %s overlap in noticia %s' % (match,
                                                                    next_match,
                                                                    self.key))
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
        self.sentence_id = sentence_id
        people_list = self.get_people_list(
            sentence_people_list[1])
        indexed = self.index_sentence(people_list)
        if indexed:
            yield self.sentence, people_list

    def get_people_list(self, id_list):
        pipe = r.pipeline()
        for id_ in id_list:
            pipe.hget('congresista:' + str(id_),
                      'nombre_ascii')
        people_list = [(str(id_), name) for id_, name in zip(
            id_list, pipe.execute())]
        return people_list

    def index_sentence(self, people_list):
        stop_words = self.load_stop_words()
        terms_tf = self.get_terms_tf(stop_words)
        indexed = False
        for person_id, person_name in people_list:
            if self.add_terms_to(terms_tf, person_id, person_name):
                indexed = True
        return indexed


    def load_stop_words(self):
        stop_words = [
            utils.remove_accents(w.decode('utf-8'))
            for w in nltk.corpus.stopwords.words(
                'spanish')]
        stop_words.extend(['presidente', 'dijo', 'senador', 'partido',
                           'representante'])
        return stop_words

    def add_terms_to(self, terms_tf, person_id, person_name):
        palabras_nombre = [p.lower() for p in person_name.split(' ')]
        person_sentences = 'indexados:congresista_oracion:%s:%s' % (
                            person_id, self.sentence_id)
        people_set = 'indexados:congresista'
        person_terms = 'indice:congresista:' + person_id
        terms_index = 'indice:term:'
        global_terms = 'indice:global'
        global_people = 'indice:congresista'
        person_sentence = r.get(person_sentences)
        indexed = False
        if person_sentence is None:
            indexed = True
            pipe = r.pipeline()
            try:
                pipe.watch(person_sentences)
                for term, tf in terms_tf.iteritems():
                    if term not in palabras_nombre:
                        pipe.zincrby(person_terms, term, tf)
                        pipe.zincrby(global_terms, term, tf)
                        pipe.zincrby(terms_index + term, person_id, 1)
                        pipe.sadd(people_set, person_id)
                pipe.set(person_sentences, True)
                pipe.zincrby(global_people, person_id, 1)
                pipe.execute()
            except redis.WatchError:
                #oracion ya indexada
                indexed= False
            finally:
                pipe.reset()
        return indexed

    def get_terms_tf(self, stopwords):
        tokenizer = nltk.RegexpTokenizer('\s+', gaps=True)
        trans_table = dict(
            (ord(symbol), u'') for symbol in string.punctuation)
        terms_tf = collections.defaultdict(float)
        for token in tokenizer.tokenize(self.sentence):
            token = unicode(token)
            token = token.translate(trans_table).strip()
            if token not in stopwords and len(token) > 1:
                terms_tf[token] += 1
        return terms_tf


if __name__ == "__main__":
    job = dumbo.Job()
    job.additer(NoticiaMapper, NoticiaReducer)
    job.additer(OracionMapper, dumbo.lib.identityreducer)
    job.run()
