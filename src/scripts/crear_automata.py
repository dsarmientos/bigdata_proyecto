import re
import pickle

i = 0

def main():
    gaceta = crear_gaceta()
    

def crear_gaceta():
    with open('lista_congresistas.pickle', 'r') as infile:
        congresistas = pickle.load(infile)
    for congresista in congresistas:
        primer_apellido, segundo_apellido = separar_apellidos(congresista['apellidos'])

def separar_apellidos(apellidos):
    mostrar = False
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
    if de_re.search(apellidos):
        apellidos = de_re.sub(reemplazo, apellidos)
        mostrar = True
    lista_apellidos = re.split(r'\s+', apellidos)
    primer_apellido = ''
    segundo_apellido = ''
    palabras = len(lista_apellidos)
    if palabras >= 1:
        primer_apellido = lista_apellidos[0].replace('_', ' ')
    if palabras >= 2:
        segundo_apellido = lista_apellidos[1].replace('_', ' ')
    if mostrar:
        print apellidos.replace('_', ' '), '[%s|%s]' % (primer_apellido, segundo_apellido)
    return primer_apellido, segundo_apellido
    
    


if __name__ == '__main__':
    main()
    