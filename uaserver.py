#!/usr/bin/python
# -*- coding: iso-8859-15 -*-


import SocketServer
import socket
import sys
import os
import time
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
listaXML = XMLHandler.get_tags()
usuario = listaXML[0][1]['username']
uaport = listaXML[1][1]['puerto']
uaip = listaXML[1][1]['ip']
audioport = listaXML[2][1]['puerto']
proxyip = listaXML[3][1]['ip']
proxyport = int(listaXML[3][1]['puerto'])
fichaudio = listaXML[5][1]['path']

def log (modo, hora, evento):
    """
    Método que imprime en un fichero los mensajes de depuración.
    """
    if modo == "inicio":
        log = listaXML[4][1]['path']
        fichero = open(log, 'a')
        fichero.write(str(hora))
        evento = evento.replace('\r\n', ' ')
        fichero.write(evento +'\r\n')
        fichero.close()
    else:
        log = listaXML[4][1]['path']
        fichero = open(log, 'a')
        fichero.write(str(hora))
        evento = evento.replace('\r\n', ' ')
        fichero.write(evento +'\r\n')
        fichero.close()

class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Clase para un servidor SIP
    """
    diccionario_rtp = {'ip_rtp': "", 'port_rtp': 0}

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
            print metodo
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
                guardar = respuesta
                lista_2 = guardar.split("\r\n")
                print lista_2
                lista_split = lista_2[7].split(" ")
                lista_split_2 = lista_2[10].split(" ")
                ip_recibe_rtp = lista_split[1]
                port_recibe_rtp = lista_split_2[1]
                self.diccionario_rtp['ip_rtp'] = ip_recibe_rtp 
                self.diccionario_rtp['port_rtp'] = port_recibe_rtp 
                print respuesta
                hora = time.time()
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport) + ": " + respuesta + '\r\n'
                log("",hora, evento)
                evento = " Received from" + str(proxyip) + ":" + str(proxyport) + ": " + line + '\r\n'
            elif metodo == "ACK":
                evento = " Received from" + str(proxyip) + ":" + str(proxyport) + ": " + line + '\r\n'
                hora = time.time()
                log("",hora, evento)
                # aEjecutar = "./mp32rtp -i " + receptor_IP + " -p " + receptor_Puerto
                print "recibido ACK"
                aEjecutar = './mp32rtp -i ' + self.diccionario_rtp['ip_rtp'] + ' -p ' + self.diccionario_rtp['port_rtp'] + " < " + fichaudio
                os.system('chmod 755 mp32rtp')
                os.system(aEjecutar)
                print(" Hemos terminado la ejecución de fichero de audio")
                print "AEJECUTAR"
                print aEjecutar
            elif metodo == "BYE":
                hora = time.time()
                respuesta = "SIP/2.0 200 OK"
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport) + ": " + respuesta + '\r\n'
                log("",hora, evento)
                evento = " Received from" + str(proxyip) + ":" + str(proxyport) + ": " + line + '\r\n'
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif not metodo in metodos:
                hora = time.time()
                respuesta = "SIP/2.0 405 Method Not Allowed"
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport) + ": " + respuesta + '\r\n'
                log("",hora, evento)
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            else:
                hora = time.time()
                respuesta = "SIP/2.0 400 Bad Request"
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport) + ": " + respuesta + '\r\n'
                log("",hora, evento)
                self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")



if __name__ == "__main__":
    """
    Procedimiento principal
    """
    serv = SocketServer.UDPServer((uaip, int(uaport)), EchoHandler)
    print "Listening..."
    serv.serve_forever()
