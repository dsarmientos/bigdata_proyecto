'''
Created on Nov 24, 2012

@author: daniel
'''
import redis
from django.shortcuts import render_to_response
from django.utils import simplejson
import logging

logger = logging.getLogger('console')

r = redis.StrictRedis(host='localhost', port=6379, db=0)


def home(request):
    random_person = get_random_person()
    words = get_top_n_terms(250, True)
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
    


def get_top_n_terms(num_terms, withscores=False):
    assert int(num_terms) > 0
    word_count = r.zrevrange('indice:global', 0, num_terms - 1, withscores)
    max_f = max((wc[1] for wc in word_count))
    f = lambda f: (f / max_f)
    word_list = [{'text':wc[0], 'size':f(wc[1])} for wc in word_count]
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


def get_top_people_words(id_list, withscores=True):
    pipe = r.pipeline(False)
    for id_ in id_list:
        pipe.zrevrange('indice:congresista:' + id_, 0, 9, withscores)
    words = pipe.execute()
    return words


def treemap(request):
    #sin presidentes
    top_people = r.zrevrange('indice:congresista', 2, -1, True)
    rows = []
    partidos = set()
    for person_id, score in top_people:
        key = 'congresista:' + person_id
        partido, nombre = r.hmget(key, 'partido_politico', 'nombre_ascii')
        if not partido:
            partido = 'Sin Partido'
        rows.append([nombre, partido, score])
        partidos.add(partido)
    table = [
        ['Congresista', 'Partido', 'Numero de palabras'],
        ['Todos', None, 0],
    ]
    table.extend([[partido, 'Todos', 0] for partido in partidos])
    table.extend(rows)
    return render_to_response(
        'treemap.html', {'treemap': simplejson.dumps(table)})
