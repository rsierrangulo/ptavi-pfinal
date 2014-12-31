#!/usr/bin/python
# -*- coding: iso-8859-15 -*-


import SocketServer
import sys
import os
import time

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

comandos = sys.argv

XML = comandos[1]

if len(comandos) != 2:
    sys.exit("Usage: python proxy_registrar.py " + XML)


# clase para etiquetas y atributos
class ExtraerXML (ContentHandler):

    def __init__(self):
        self.taglist = []
        self.tags = ['server', 'database', 'log']
        self.attributes = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']}

    def startElement(self, tag, attrs):
        dictionary = {}
        # si existe la etiqueta en mi lista de etiquetas.
        if tag in self.tags: 
            # recorro todos los atributos y los guardo en mi diccionario.
            for attribute in self.attributes[tag]:
                if attribute == 'ip':
                    dictionary[attribute] = attrs.get(attribute, "")
                    ipserver = dictionary[attribute]
                    if ipserver == "":
                        ipserver = "127.0.0.1"
                else:
                    dictionary[attribute] = attrs.get(attribute, "")
            # voy encadenando la lista, guardo a continuación sin sustituir lo que tiene dentro.
            self.taglist.append([tag, dictionary])

    def get_tags(self):
        return self.taglist

parser = make_parser()
XMLHandler = ExtraerXML()
parser.setContentHandler(XMLHandler)
parser.parse(open(XML))
listaXML = XMLHandler.get_tags()
usuario = listaXML[0][1]['name']
ipserver = listaXML[0][1]['ip']
portserver = listaXML[0][1]['puerto']


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """

    diccionario_user = {}
    lista_user = []


def handle(self):
        """
        Método handle
        """
        CLIENT = str(self.client_address[0])
        while 1:
            line = self.rfile.read()
            if not line:
                break
            print "El cliente nos manda " + line
            lista = line.split(" ")
            lista_split = lista[1].split(" ")
            print lista_split
            metodo = lista[0]
            metodos = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            if metodo == "REGISTER":
                tiempo = time.time() + float(lista[3])
                tiempo_actual = time.time()
                self.lista_user = [self.client_address[0], tiempo]
                self.diccionario_user[lista[1]] = self.lista_user
                for usuario in self.diccionario_user.keys():
                    if self.diccionario_user[usuario][1] < tiempo_actual:
                        del self.diccionario_user[usuario]
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif metodo == "INVITE":
                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(respuesta)
            elif not metodo in metodos:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            else:
                self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")

    def register2file(self):
        """
        Método que imprime en el fichero el contenido del diccionario
        """
        DATABASE = lista[1][1]['path']
        fichero = open(DATABASE, 'w')
        fichero.write("User" + '\t\t\t' + "IP" + '\t\t\t' + "Port" + '\t\t\t' + "Time" + '\t\t\t' + "Expires" + '\r\n')
        for user in self.diccionario_user.keys():
            # El user se imprime como "sip:usuario" debido a que se guarda así
            # en la lista
            IP = self.diccionario_user[user][0]
            port = self.diccionario_user[user][1]
            hora = self.diccionario_user[user][2]
            expires = self.diccionario_user[user][3]
            fichero.write(user + '\t' + IP + '\t' + port + '\t' + hora + '\t' + expires + '\t')
            hora = time.gmtime(self.diccionario_user[usuario][2])
            fichero.write(time.strftime('%Y-%m-%d %H:%M:%S', hora) + '\r\n')
        fichero.close()

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((proxyip, proxyport))
           

serv = SocketServer.UDPServer(("", int(portserver)), SIPRegisterHandler)
sys.exit("Server " + usuario + " listening at port " + portserver + "...")
serv.serve_forever()



