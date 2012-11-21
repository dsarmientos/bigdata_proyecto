import re
import pickle

import ahocorasick

import unicodedata


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    only_ascii = nkfd_form.encode('ASCII', 'ignore')
    return only_ascii

def get_automata():
    gaceta = crear_gaceta()
    automata = ahocorasick.KeywordTree()
    agregar_nombres(automata, gaceta)
    automata.make()
    return automata
    

def crear_gaceta():
    with open('lista_congresistas.pickle', 'r') as infile:
        congresistas = pickle.load(infile)
    for congresista in congresistas:
        expandir_nombres(congresista)
    return congresistas
        

def expandir_nombres(congresista):
    primer_apellido, segundo_apellido = separar_nombres(
            congresista['apellidos'])
    primer_nombre, segundo_nombre = separar_nombres(
            congresista['nombres'])
    congresista['primer_nombre'] = primer_nombre
    congresista['segundo_nombre'] = segundo_nombre
    congresista['primer_apellido'] = primer_apellido
    congresista['segundo_apellido'] = segundo_apellido


def separar_nombres(nombres):
    def reemplazo(match):
        izq = match.group(1).strip()
        sep = match.group(2).strip().lower()
        if sep == 'de la':
            sep = 'de_la' 
        elif sep == 'de los':
            sep = 'de_los' 
        der = match.group(3).strip()
        txt = '%s %s_%s' % (izq, sep, der)
        return txt.strip()
    de_re = re.compile('(^|\w+\s+)(de la|de los|del?)\s+(\w+)', re.I)
    if de_re.search(nombres):
        nombres = de_re.sub(reemplazo, nombres)
    lista_nombres = re.split(r'\s+', nombres)
    primer_nombre = ''
    segundo_nombre = ''
    palabras = len(lista_nombres)
    if palabras >= 1:
        primer_nombre = lista_nombres[0].replace('_', ' ')
    if palabras >= 2:
        segundo_nombre = lista_nombres[1].replace('_', ' ')
    return primer_nombre, segundo_nombre


def agregar_nombres(automata, gaceta):
    for congresista in gaceta:
        automata.add(
           remove_accents(u'%s %s %s' % (congresista['primer_nombre'], 
                          congresista['primer_apellido'],
                          congresista['segundo_apellido']))
         )
        automata.add(
           remove_accents(u'%s %s' % (congresista['nombres'], 
                       congresista['apellidos']))
         )


def guardar_automata(automata):
    with open('automata.pickle', 'w') as outfile:
        pickle.dump(automata, outfile)