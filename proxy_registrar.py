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
    sys.exit('Usage: python proxy_registrar.py config')

XML = comandos[1]


def log(modo, hora, evento):
    """
    Método que imprime en un fichero los mensajes de depuración.
    """
    if modo == "inicio":
        log = listaXML[2][1]['path']
        fichero = open(log, 'a')
        hora = time.gmtime(float(hora))
        fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
        evento = evento.replace('\r\n', ' ')
        fichero.write(evento + '\r\n')
        fichero.close()
    else:
        log = listaXML[2][1]['path']
        fichero = open(log, 'a')
        hora = time.gmtime(float(hora))
        fichero.write(time.strftime('%Y%m%d%H%M%S', hora))
        evento = evento.replace('\r\n', ' ')
        fichero.write(evento + '\r\n')
        fichero.close()


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
                    # si la ip esta vacía meto 121.0.0.1
                    ipserver = dictionary[attribute]
                    if ipserver == "":
                        ipserver = "127.0.0.1"
                else:
                    dictionary[attribute] = attrs.get(attribute, "")
            # voy encadenando la lista, guardo a continuación sin sustituir
            #lo que tiene dentro.
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

evento = " Starting... " + '\r\n'
hora = time.time()
log("inicio", hora, evento)


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    Echo server class
    """

    diccionario_user = {}
    lista_user = []

    def register2file(self):
        """
        Método que imprime en un fichero el contenido del diccionario
        """
        database = listaXML[1][1]['path']
        fichero = open(database, 'w')
        titulo = "User" + '\t\t\t\t' + "IP" + '\t\t\t' + "Port" + '\t' + "Time"
        titulo += '\r\n'
        fichero.write(titulo)
        for user in self.diccionario_user.keys():
            # El user se imprime como "sip:usuario" debido a que se guarda así
            # en la lista
            IP = self.diccionario_user[user][0]
            port = self.diccionario_user[user][2]
            hora = self.diccionario_user[user][1]
            fichero.write(user + '\t' + IP + '\t' + port + '\t')
            hora = time.gmtime(hora)
            fichero.write(time.strftime('%Y-%m-%d %H:%M:%S', hora) + '\r\n')
        fichero.close()

    def handle(self):
        """
        Método handle
        """
        while 1:
            line = self.rfile.read()
            if not line:
                break
            print "RECIBIDO " + line
            lista = line.split(" ")
            lista_split = lista[1].split(":")
            IP = self.client_address[0]
            metodo = lista[0]
            metodos = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            if metodo == "REGISTER":
                tiempo = time.time() + float(lista[3])
                tiempo_actual = time.time()
                # creo una lista ordenada que contiene ip, tiempo y puerto.
                self.lista_user = [IP, tiempo, lista_split[2]]
                # guardo la ip, el tiempo de expiracion y el puerto en esa
                # clave del diccionario.
                self.diccionario_user[lista_split[1]] = self.lista_user
                for usuario in self.diccionario_user.keys():
                    # si el tiempo actual es menor que el tiempo guardado
                    # en el diccionario
                    if self.diccionario_user[usuario][1] < tiempo_actual:
                        # borro el usuario (clave + valor) del diccionario
                        del self.diccionario_user[usuario]
                evento = " Received from " + str(IP) + ":"
                evento += str(lista_split[2]) + ": " + line + '\r\n'
                hora = time.time()
                log("", hora, evento)
                evento = " Sent to " + str(IP) + ":" + str(lista_split[2])
                evento += ": SIP/2.0 200 OK" + '\r\n'
                log("", hora, evento)
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif metodo == "INVITE":
                nombre = lista[1]
                nombre_split = nombre.split(":")
                nombre_usuario = nombre_split[1]
                # miro si esta registrado y si lo está, reenvio el line.
                if nombre_usuario in self.diccionario_user:
                    uaip = self.diccionario_user[nombre_usuario][0]
                    uaport = self.diccionario_user[nombre_usuario][2]
                    # con la dirección sip saco la ip y el puerto del
                    # diccionario.
                    my_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM)
                    my_socket.setsockopt(
                        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_socket.connect((uaip, int(uaport)))
                    my_socket.send(line)
                    #Busco la ip origen
                    ip_receive = self.client_address[0]
                    port_receive = self.client_address[1]
                    hora = time.time()
                    evento = " Received from " + str(ip_receive) + ":"
                    evento += str(port_receive) + ": " + line + '\r\n'
                    log("", hora, evento)
                    hora = time.time()
                    evento = " Sent to " + str(uaip) + " " + str(uaport) + " "
                    evento += line + '\r\n'
                    log("", hora, evento)
                    data = my_socket.recv(1024)
                    print data
                    self.wfile.write(data)
                else:
                    ip_receive = self.client_address[0]
                    puerto_receive = self.client_address[1]
                    hora = time.time()
                    evento = " Received from " + str(ip_receive) + ":"
                    evento += str(port_receive) + ": " + line + '\r\n'
                    log("", hora, evento)
                    print "El usuario no está registrado"
                    self.wfile.write("SIP/2.0 404 User Not Found\r\n")
                    hora = time.time()
                    error = " SIP/2.0 404 User Not Found"
                    evento = " Error: " + error + '\r\n'
                    log("", hora, evento)
            elif metodo == "BYE":
                nombre = lista[1]
                nombre_split = nombre.split(":")
                nombre_usuario = nombre_split[1]
                uaip = self.diccionario_user[nombre_usuario][0]
                uaport = self.diccionario_user[nombre_usuario][2]
                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_socket.connect((uaip, int(uaport)))
                my_socket.send(line)
                ip_receive = self.client_address[0]
                port_receive = self.client_address[1]
                hora = time.time()
                evento = " Received from " + str(ip_receive) + ":"
                evento += str(port_receive) + ": " + line + '\r\n'
                log("", hora, evento)
                evento = " Sent to " + str(uaip) + ":" + str(uaport) + ": "
                evento += line + '\r\n'
                log("", hora, evento)
                data = my_socket.recv(1024)
                self.wfile.write(data)
            elif metodo == "ACK":
                nombre = lista[1]
                nombre_split = nombre.split(":")
                nombre_usuario = nombre_split[1]
                uaip = self.diccionario_user[nombre_usuario][0]
                uaport = self.diccionario_user[nombre_usuario][2]
                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_socket.connect((uaip, int(uaport)))
                my_socket.send(line)
                ip_receive = self.client_address[0]
                port_receive = self.client_address[1]
                hora = time.time()
                evento = " Received from " + str(ip_receive) + ":"
                evento += str(port_receive) + ": " + line + '\r\n'
                log("", hora, evento)
                evento = " Sent to " + str(uaip) + ":" + str(uaport) + ": "
                evento += line + '\r\n'
                log("", hora, evento)
            self.register2file()


if __name__ == "__main__":
    ip = ipserver
    port = portserver
    serv = SocketServer.UDPServer((ip, int(port)), SIPRegisterHandler)
    hora = time.time()
    evento = " Server " + usuario + " listening at port " + portserver + "..."
    log("", hora, evento)
    print "Server " + usuario + " listening at port " + portserver + "..."
    serv.serve_forever()
