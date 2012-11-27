#encoding=utf-8

'''
Created on Nov 24, 2012

@author: daniel
'''
import logging
import math
import os
import unicodedata

import redis
from django.shortcuts import render_to_response
from django.utils import simplejson
import nltk

logger = logging.getLogger('console')

r = redis.StrictRedis(host='localhost', port=6379, db=0)


def home(request):
    random_person = get_random_person()
    words = get_top_n_terms(500, True)
    id_list = get_top_n_people(9, False)
    names = get_people_name(id_list)
    images = get_people_image(id_list)
    people_words = get_top_people_words(id_list)
    people = []
    for i, person_id in enumerate(id_list):
        if images[i]:
            image = 'http://congresovisible.org' + images[i]
        else:
            image = '/static/img/imagen-perfil.jpg'
        people.append(
            {'nombre':' '.join(names[i]), 'pk':person_id,
             'palabras': people_words[i], 'imagen':image})
    return render_to_response(
        'index.html',
        {'words': simplejson.dumps(words), 'congresistas':people,
         'random_person':random_person})


def get_random_person():
    pk = r.srandmember('indexados:congresista')
    pipe = r.pipeline(False)
    pipe.hmget('congresista:' + pk, 'nombres', 'apellidos', 'imagen')
    pipe.zrevrange('indice:congresista:' + pk, 0, 0)
    pipe.zrevrank('indice:congresista', pk)
    result = pipe.execute()
    nombres_imagen, top_word, rank = result
    nombres = nombres_imagen[:-1]
    imagen = nombres_imagen[-1]
    if imagen:
        imagen = 'http://congresovisible.org' +  imagen
    else:
        imagen = '/static/img/imagen-perfil.jpg'
    return {'pk': pk, 'nombre': ' '.join(nombres), 'top_word':top_word[0],
            'rank': rank, 'imagen':imagen}

f = lambda f, max_f: (f / max_f)


def get_top_n_terms(num_terms, withscores=False):
    assert int(num_terms) > 0
    word_count = r.zrevrange('indice:global', 0, num_terms - 1, withscores)
    max_f = max((wc[1] for wc in word_count))
    word_list = [{'text':wc[0], 'size':f(wc[1], max_f), 'n':wc[1]} for wc in word_count]
    for w in word_list:
        assert w['size'] <= 1 and w['size'] > 0
    return word_list
    

def get_top_n_people(num_people, withscores=False):
    assert int(num_people) > 0
    people_score = r.zrevrange('indice:congresista', 0, num_people - 1, withscores)
    return people_score


def get_people_name(id_list):
    pipe = r.pipeline(False)
    for id_ in id_list:
        pipe.hmget('congresista:' + id_, 'nombres', 'apellidos')
    names = pipe.execute()
    return names


def get_people_image(id_list):
    pipe = r.pipeline(False)
    for id_ in id_list:
        pipe.hget('congresista:' + id_, 'imagen')
    imgs = pipe.execute()
    return imgs


def get_top_people_words(id_list, withscores=True, n=10):
    assert n >= 0
    pipe = r.pipeline(False)
    for id_ in id_list:
        pipe.zrevrange('indice:congresista:' + id_, 0, n - 1, withscores)
    words = pipe.execute()
    return words


def treemap(request):
    #sin presidentes
    top_people = r.zrevrange('indice:congresista', 2, -1, True)
    rows = []
    partidos = set()
    table = [
        ['Congresista', 'Partido', 'Número de palabras'],
        ['Todos', None, 0],
    ]
    for person_id, score in top_people:
        key = 'congresista:' + person_id
        partido, nombre = r.hmget(key, 'partido_politico', 'nombre_ascii')
        if not partido:
            partido = 'Sin Partido'
        rows.append([nombre, partido, score])
        partidos.add(partido)
    table.extend([[partido, 'Todos', 0] for partido in partidos])
    table.extend(rows)
    return render_to_response(
        'treemap.html', {'treemap': simplejson.dumps(table)})

def combochart(request):
    #sin presidentes
    top_people = r.zrevrange('indice:congresista', 2, -1, True)
    rows = {}
    for person_id, score in top_people:
        key = 'congresista:' + person_id
        partido = r.hget(key, 'partido_politico')
        if not partido:
            partido = 'Sin Partido'
        if partido not in rows:
            rows[partido]= {
                'partido': partido,
                'top_score': score,
                'total': score,
                'num_people': 1,
            }
        else:
            rows[partido]['total'] += score
            rows[partido]['num_people'] += 1
    table = [
        ['Partido', 'Total', 'Congresista MP', 'Promedio'],
    ]
    for row in sorted(rows.values(), key=lambda r: r['total'], reverse=True)[:7]:
        table.append([row['partido'], row['total'], row['top_score'], row['total'] / row['num_people']])
    return render_to_response(
        'combochart.html', {'table': simplejson.dumps(table)})


def buscar(request):
    resultados = []
    q = 'Buscar'
    if 'q' in request.GET: 
        q = request.GET.get('q') 
        terms = extract_terms(q)
        results = search(terms)
        if results:
            resultados = get_related_people_info(results, None)
    return render_to_response('search.html', {'resultados': resultados, 'q':q})


def perfil_congresista(request, congresista_id):
    id_list = [congresista_id,]
    name = get_people_name(id_list)[0]
    image = get_people_image(id_list)[0]
    words = get_top_people_words(id_list, n=350)[0]
    max_f = max((wc[1] for wc in words))
    word_list = [{'text':wc[0], 'size':f(wc[1], max_f), 'n':wc[1]} for wc in words]
    terms = [w[0] for w in words[1:11]]
    related_people = get_related_people(terms, congresista_id)
    if image:
        image = 'http://congresovisible.org' + image
    else:
        image = '/static/img/imagen-perfil.jpg'
    congresista = {'nombre':' '.join(name), 'pk':congresista_id,
                   'imagen':image}
    return render_to_response(
        'perfil_congresista.html',
        {'words': simplejson.dumps(word_list), 'congresista':congresista, 'related':related_people})

 
def get_related_people(terms, congresista_id):
    related = search(terms, 0, 6)
    with_info = get_related_people_info(related, congresista_id)
    return with_info


def get_related_people_info(related, congresista_id):
    names = get_people_name(related)
    images = get_people_image(related)
    related_people = []
    for i, person_id in enumerate(related):
        if person_id == congresista_id: continue
        if images[i]:
            image = 'http://congresovisible.org' + images[i]
        else:
            image = '/static/img/imagen-perfil.jpg'
        related_people.append(
            {'nombre':' '.join(names[i]), 'pk':person_id,
             'imagen':image})
    return related_people



def search(terms, offset=0, count=10):
    if not terms:
        return False

    def idf(count):
        # Calculate the IDF for this particular count
        if not count:
            return 0
        return max(math.log(total_docs / count, 2), 0)

    total_docs = max(r.scard('indexados:congresista'), 1)

    # Get our document frequency values...
    pipe = r.pipeline(False)
    for term in terms:
        pipe.zcard('indice:term:' + term)
    sizes = pipe.execute()

    # Calculate the inverse document frequencies...
    idfs = map(idf, sizes)

    # And generate the weight dictionary for passing to zunionstore.
    weights = dict((key, idfv)
            for key, size, idfv in zip(('indice:term:'+t for t in terms), sizes, idfs) if size)

    if not weights:
        return False

    # Generate a temporary result storage key
    temp_key = 'temp:' + os.urandom(8).encode('hex')
    try:
        # Actually perform the union to combine the scores.
        r.zunionstore(temp_key, weights)
        # Get the results.
        ids = r.zrevrange(
            temp_key, offset, offset+count-1)
    finally:
        # Clean up after ourselves.
        r.delete(temp_key)
    return ids


def extract_terms(query):
    stop_words = [
        remove_accents(w.decode('utf-8'))
        for w in nltk.corpus.stopwords.words(
                'spanish')]
    query = (remove_accents(w.lower()) for w in query.split(' '))
    terms = []
    for term in query:
        if term not in stop_words:
            terms.append(term)
    return terms


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return only_ascii