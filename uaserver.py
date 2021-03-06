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

if len(comandos) != 2:
    sys.exit('Usage: python uaserver.py config')

XML = comandos[1]


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
fichaudio = listaXML[5][1]['path']

# si la ip esta vacia meto la direccion 127.0.0.1
if uaip == "":
    uaip = '127.0.0.1'


def log(modo, hora, evento):
    """
    Método que imprime en un fichero los mensajes de depuración.
    """
    if modo == "inicio":
        log = listaXML[4][1]['path']
        fichero = open(log, 'a')
        hora = time.gmtime(float(hora))
        fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
        evento = evento.replace('\r\n', ' ')
        fichero.write(evento + '\r\n')
        fichero.close()
    else:
        log = listaXML[4][1]['path']
        fichero = open(log, 'a')
        hora = time.gmtime(float(hora))
        fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
        evento = evento.replace('\r\n', ' ')
        fichero.write(evento + '\r\n')
        fichero.close()

evento = " Starting... " + '\r\n'
hora = time.time()
log("inicio", hora, evento)


class EchoHandler(SocketServer.DatagramRequestHandler):
    """
    Clase para un servidor SIP
    """
    # creo un diccionario como variable global para guardar la ip y el puerto
    # para el envio rtp
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
            if metodo == "INVITE":
                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\n"
                respuesta += "Content-Type: application/sdp\r\n\r\n"
                respuesta += "v=0\r\n"
                respuesta += "o=" + usuario + " " + uaip + "\r\n"
                respuesta += "s=misesion\r\n"
                respuesta += "t=0\r\n"
                respuesta += "m=audio8 " + audioport + " RTP\r\n\r\n"
                self.wfile.write(respuesta)
                guardar = line
                lista_2 = guardar.split("\r\n")
                # busco en el mensaje que recibo la ip y el puerto donde voy a
                # enviar el rtp
                lista_split = lista_2[4].split(" ")
                lista_split_2 = lista_2[7].split(" ")
                ip_recibe_rtp = lista_split[1]
                port_recibe_rtp = lista_split_2[1]
                self.diccionario_rtp['ip_rtp'] = ip_recibe_rtp
                self.diccionario_rtp['port_rtp'] = port_recibe_rtp
                hora = time.time()
                evento = " Received from " + str(proxyip) + ":"
                evento += str(proxyport) + ": " + line + '\r\n'
                log("", hora, evento)
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport)
                evento += ": " + respuesta + '\r\n'
                log("", hora, evento)
            elif metodo == "ACK":
                evento = " Received from " + str(proxyip) + ":"
                evento += str(proxyport) + ": " + line + '\r\n'
                hora = time.time()
                log("", hora, evento)
                print "Recibido ACK"
                aEjecutar = './mp32rtp -i ' + self.diccionario_rtp['ip_rtp']
                aEjecutar += ' -p ' + self.diccionario_rtp['port_rtp'] + " < "
                aEjecutar += fichaudio
                os.system('chmod 755 mp32rtp')
                os.system(aEjecutar)
                hora = time.time()
                linea = "Envio RTP"
                ip = self.diccionario_rtp['ip_rtp']
                port = self.diccionario_rtp['port_rtp']
                evento = " Sent to " + str(ip) + ":" + str(port)
                evento += ": " + linea + '\r\n'
                log("", hora, evento)
                print("Hemos terminado la ejecución de fichero de audio")
            elif metodo == "BYE":
                hora = time.time()
                evento = " Received from " + str(proxyip) + ":"
                evento += str(proxyport) + ": " + line + '\r\n'
                log("", hora, evento)
                respuesta = "SIP/2.0 200 OK"
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport)
                evento += ": " + respuesta + '\r\n'
                log("", hora, evento)
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif not metodo in metodos:
                hora = time.time()
                respuesta = "SIP/2.0 405 Method Not Allowed"
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport)
                evento += ": " + respuesta + '\r\n'
                log("", hora, evento)
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            else:
                hora = time.time()
                respuesta = "SIP/2.0 400 Bad Request"
                evento = " Sent to " + str(proxyip) + ":" + str(proxyport)
                evento += ": " + respuesta + '\r\n'
                log("", hora, evento)
                self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")


if __name__ == "__main__":
    """
    Procedimiento principal
    """
    serv = SocketServer.UDPServer((uaip, int(uaport)), EchoHandler)
    print "Listening..."
    serv.serve_forever()
