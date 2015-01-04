#!/usr/bin/python
# -*- coding: iso-8859-15 -*-


import SocketServer
import socket
import sys
import os
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

comandos = sys.argv

XML = comandos[1]

if len(comandos) != 2:
    sys.exit("Usage: python uaserver.py " + XML)

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
usuario = lista[0][1]['username']
uaport = lista[1][1]['puerto']
uaip = lista[1][1]['ip']
audioport = lista[2][1]['puerto']
proxyip = lista[3][1]['ip']
proxyport = int(lista[3][1]['puerto'])
fichaudio = lista[5][1]['path']


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Clase para un servidor SIP
    """
    guardar = ""
    def handle(self):
        """
        Método handle
        """

        while 1:
            line = self.rfile.read()
            if not line:
                break
            print "RECIBIDO ", line
            lista = line.split(" ")

            metodo = lista[0]            
            metodos = ['INVITE', 'ACK', 'BYE']

            if metodo == "INVITE":
                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\n"
                respuesta += "Content-Type: application/sdp\r\n"
                respuesta += "v=0\r\n"
                respuesta += "o=" + usuario + " " + uaip + "\r\n"
                respuesta += "s=misesion\r\n"
                respuesta += "t=0\r\n"
                respuesta += "m=audio8 " + audioport + " RTP\r\n\r\n"
                self.wfile.write(respuesta)
                self.guardar = respuesta
                lista_2 = self.guardar.split("\r\n")
                print lista_2
                lista_split = lista_2[7].split(" ")
                lista_split_2 = lista_2[10].split(" ")
                ip_recibe = lista_split[1]
                port_recibe = lista_split_2[1]
                print "TRAZAS"
                print ip_recibe
                print port_recibe
                print "TRAZAS"
                print respuesta
            elif metodo == "ACK":
                # aEjecutar = "./mp32rtp -i " + receptor_IP + " -p " + receptor_Puerto
                aEjecutar = './mp32rtp -i' + ip_recibe + '-p' + port_recibe + "<" + fichaudio
                os.system('chmod 755 mp32rtp')
                os.system(aEjecutar)
                print(" Hemos terminado la ejecución de fichero de audio")
            elif metodo == "BYE":
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif not metodo in metodos:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            else:
                self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")



if __name__ == "__main__":
    """
    Procedimiento principal
    """
    serv = SocketServer.UDPServer((uaip, int(uaport)), EchoHandler)
    print "Listening..."
    serv.serve_forever()
