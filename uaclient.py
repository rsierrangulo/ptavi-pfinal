#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
import os
import time
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

comandos = sys.argv

if len(comandos) != 4:
    sys.exit('Usage: python uaclient.py config method option')

XML = comandos[1]
METODO = comandos[2].upper()
OPTION = comandos[3]


# clase para etiquetas y atributos
class ExtraerXML (ContentHandler):

    def __init__(self):
        self.taglist = []
        self.tags = [
            'account', 'uaserver', 'rtpaudio', 'regproxy', 'log', 'audio']
        self.attributes = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']}

    def startElement(self, tag, attrs):
        dictionary = {}
        # si existe la etiqueta en mi lista de etiquetas.
        if tag in self.tags:
            # recorro todos los atributos y los guardo en mi diccionario.
            for attribute in self.attributes[tag]:
                dictionary[attribute] = attrs.get(attribute, "")
            # voy encadenando la lista, guardo a continuación sin sustituir
            # lo que tiene dentro.
            self.taglist.append([tag, dictionary])

    def get_tags(self):
        return self.taglist

parser = make_parser()
XMLHandler = ExtraerXML()
parser.setContentHandler(XMLHandler)
parser.parse(open(XML))
listaXML = XMLHandler.get_tags()
usuario = listaXML[0][1]['username']
uaport = listaXML[1][1]['puerto']
uaip = listaXML[1][1]['ip']
audioport = listaXML[2][1]['puerto']
proxyip = listaXML[3][1]['ip']
proxyport = int(listaXML[3][1]['puerto'])
# si la ip esta vacia meto la direccion 127.0.0.1
if uaip == "":
    uaip = '127.0.0.1'


def log(modo, hora, evento):
    """
    Método que imprime en un fichero los mensajes de depuración.
    """
    log = listaXML[4][1]['path']
    fichero = open(log, 'a')
    hora = time.gmtime(float(hora))
    fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
    evento = evento.replace('\r\n', ' ')
    fichero.write(evento + '\r\n')
    fichero.close()

if METODO == 'REGISTER':
    # [1] porque es el diccionario y no la etiqueta
    #REGISTER sip:leonard@bigbang.org:1234 SIP/2.0
    #Expires: 3600
    LINE = METODO + " sip:" + usuario + ":" + uaport + ": SIP/2.0\r\n"
    LINE += "Expires: " + OPTION + "\r\n\r\n"
    hora = time.time()
    evento = " Sent to " + str(proxyip) + ":" + str(proxyport)
    evento += ": " + LINE + '\r\n'
    log("", hora, evento)
elif METODO == 'INVITE':
    # INVITE sip:penny@girlnextdoor.com SIP/2.0
    #Content-Type: application/sdp
    #v=0
    #o=leonard@bigbang.org 127.0.0.1
    #s=misesion
    #t=0
    #m=audio 34543 RTP
    LINE = METODO + " sip:" + OPTION + " SIP/2.0\r\n"
    LINE += "Content-Type: application/sdp\r\n\r\n"
    LINE += "v=0\r\n"
    LINE += "o=" + usuario + " " + uaip + "\r\n"
    LINE += "s=misesion\r\n"
    LINE += "t=0\r\n"
    LINE += "m=audio8 " + audioport + " RTP\r\n\r\n"
    hora = time.time()
    evento = " Sent to " + str(proxyip) + ":" + str(proxyport)
    evento += ": " + LINE + '\r\n'
    log("", hora, evento)
    lista = LINE.split(" ")
elif METODO == 'BYE':
    LINE = METODO + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
    hora = time.time()
    evento = " Sent to " + str(proxyip) + ":" + str(proxyport)
    evento += ": " + LINE + '\r\n'
    log("", hora, evento)
else:
    hora = time.time()
    error = "SIP/2.0 405 Method Not Allowed"
    evento = " Error: " + error + '\r\n'
    log("", hora, evento)
    sys.exit("Error: Método no válido")

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((proxyip, proxyport))

try:
    print "Enviando: " + LINE
    my_socket.send(LINE)

    data = my_socket.recv(1024)

    if data == "SIP/2.0 200 OK\r\n\r\n":
        evento = " Received from " + str(proxyip) + ":" + str(proxyport)
        evento += ": " + data + '\r\n'
        hora = time.time()
        log("", hora, evento)
    elif data == "SIP/2.0 405 Method Not Allowed\r\n\r\n":
        evento = " Error: " + data + '\r\n'
        hora = time.time()
        log("", hora, evento)
    elif data == "SIP/2.0 400 Bad Request\r\n\r\n":
        evento = " Error: " + data + '\r\n'
        hora = time.time()
        log("", hora, evento)

    print 'Recibido -- ', data
    recibe = data.split('\r\n')
    print recibe
    if len(recibe) == 14:
        evento = " Received from " + str(proxyip) + ":" + str(proxyport)
        evento += ": " + data + '\r\n'
        hora = time.time()
        log("", hora, evento)
        fichaudio = listaXML[5][1]['path']
        # saco del recibe ip y puerto donde mandar
        split_recibe = recibe[8].split(" ")
        ip_recibe = split_recibe[1]
        split_recibe_1 = recibe[11].split(" ")
        port_recibe = split_recibe_1[1]
        #Envio ACK
        ACK = "ACK sip:" + OPTION + " SIP/2.0\r\n\r\n"
        hora = time.time()
        evento = " Sent to " + str(proxyip) + ":" + str(proxyport) + ": "
        evento += ACK + '\r\n'
        log("", hora, evento)
        print "Enviando ACK: " + ACK
        my_socket.send(ACK)
        aEjecutar = './mp32rtp -i ' + str(ip_recibe) + ' -p ' + port_recibe
        aEjecutar += " < " + fichaudio
        os.system('chmod 755 mp32rtp')
        os.system(aEjecutar)
        linea = "Envio de RTP"
        evento = " Sent to " + str(ip_recibe) + ":" + str(port_recibe) + ": "
        evento += linea + '\r\n'
        log("", hora, evento)
        data = my_socket.recv(1024)

    hora = time.time()
    evento = "Finishing."
    log = ("", hora, evento)
    print "Terminando socket..."
except socket.error:
    hora = time.time()
    evento = "Error: No server listening at " + uaip + " port " + str(uaport)
    log("", hora, evento)
