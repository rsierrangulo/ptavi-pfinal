#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Programa cliente que abre un socket a un servidor
"""

import socket
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

comandos = sys.argv

if len(comandos) != 4:
    sys.exit('Usage: python uaclient.py config method option')


XML = comandos[1]
METODO = comandos[2].upper()
OPTION = comandos [3]

# clase para etiquetas y atributos
class ExtraerXML (ContentHandler):

    def __init__(self):
        self.taglist = []
        self.tags = ['account', 'uaserver', 'rtpaudio', 'regproxy', 'log', 'audio']
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
            # voy encadenando la lista, guardo a continuación sin sustituir lo que tiene dentro.
            self.taglist.append([tag, dictionary])

    def get_tags(self):
        return self.taglist

parser = make_parser()
XMLHandler = ExtraerXML()
parser.setContentHandler(XMLHandler)
parser.parse(open(XML))
lista = XMLHandler.get_tags()

if METODO == 'REGISTER':
    # [1] porque es el diccionario y no la etiqueta
    #REGISTER sip:leonard@bigbang.org:1234 SIP/2.0
    #Expires: 3600
    LINE = METODO + " sip:" + lista[0][1]['username'] + ":" + lista[1][1]['puerto'] + " SIP/2.0\r\n"
    LINE += "Expires: " + OPTION
elif METODO == 'INVITE':
    # INVITE sip:penny@girlnextdoor.com SIP/2.0
    #Content-Type: application/sdp
    #v=0
    #o=leonard@bigbang.org 127.0.0.1
    #s=misesion
    #t=0
    #m=audio 34543 RTP
    CLIENT = str(client_address[0])
    LINE = METODO + " sip:" + OPTION  + " SIP/2.0\r\n\r\n"
    LINE += "Content-Type: application/sdp\r\n\r\n"
    LINE += "v=0\r\n\r\n"
    LINE += "o=" + lista[0][1]['username'] + CLIENT + "\r\n\r\n"
    LINE += "s=misesion\r\n\r\n"
    LINE += "t=0\r\n\r\n"
    LINE += "m=audio" + lista[2][1]['puerto'] + "RTP\r\n\r\n"
elif METODO == 'BYE':
    LINE = METODO + " sip:" + lista[0][1]['username'] + lista[1][1]['puerto'] + "SIP/2.0\r\n\r\n"

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((lista[1][1]['ip'], int(lista[1][1]['puerto'])))

try:
    print "Enviando: " + LINE
    my_socket.send(LINE)

    data = my_socket.recv(1024)

    print 'Recibido -- ', data

    respuesta = "SIP/2.0 100 Trying\r\n\r\n"
    respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
    respuesta += "SIP/2.0 200 OK\r\n\r\n"

    if data == respuesta:
        ACK = "ACK" + " sip:" + LOGIN + "@" + SERVER + " SIP/2.0\r\n\r\n"
        print "Enviando ACK: " + ACK
        my_socket.send(ACK)
        data = my_socket.recv(1024)

    print "Terminando socket..."
except socket.error:
    print "Error: No server listening at " + lista[1][1]['ip'] + " port " + str(lista[1][1]['puerto'])





