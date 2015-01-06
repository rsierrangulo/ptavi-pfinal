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
    sys.exit("Usage: python proxy_registrar.py " + XML)


def log (hora, evento):
    """
    Método que imprime en un fichero los mensajes de depuración.
    """
    log = listaXML[2][1]['path']
    fichero = open('log', 'a')
    fichero.write("Tiempo" + '\t\t\t\t\t\t\t\t' + "Evento" + '\r\n')
    fichero.write(str(hora))
    fichero.write(evento)
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

    def register2file(self):
        """
        Método que imprime en un fichero el contenido del diccionario
        """
        database = listaXML[1][1]['path']
        fichero = open('database', 'w')
        fichero.write("User" + '\t\t\t\t' + "IP" + '\t\t\t' + "Port" + '\t' + "Time" + '\r\n')
        print self.diccionario_user
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
        hora = time.time()
        evento = " Starting..."
        log(hora, evento)
        while 1:
            line = self.rfile.read()
            if not line:
                break
            print "RECIBIDO " + line
            lista = line.split(" ")
            lista_split = lista[1].split(":")
            IP = self.client_address[0]
            print lista_split
            
            metodo = lista[0]
            metodos = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            if metodo == "REGISTER":
                tiempo = time.time() + float(lista[3])
                tiempo_actual = time.time()
                # creo una lista ordenada que contiene ip, tiempo y puerto.
                self.lista_user = [IP, tiempo, lista_split[2]]
                # guardo la ip, el tiempo de expiracion y el puerto en esa clave del diccionario.
                self.diccionario_user[lista_split[1]] = self.lista_user
                for usuario in self.diccionario_user.keys():
                    # si el tiempo actual es menor que el tiempo guardado en el diccionario 
                    if self.diccionario_user[usuario][1] < tiempo_actual:
                        # borro el usuario (clave + valor) del diccionario
                        del self.diccionario_user[usuario]
                print self.diccionario_user
                evento = " Received from " + str(IP) + " " + str(lista_split[2]) + " " + line + '\r\n'
                hora = time.time()
                log(hora, evento)
                evento = " Sent to " + str(IP) + " " + str(lista_split[2]) + " SIP/2.0 200 OK"  + '\r\n'
                log(hora, evento)
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
            elif metodo == "INVITE":
                nombre = lista[1]
                nombre_split= nombre.split(":") 
                nombre_usuario = nombre_split[1]
                # miro si esta registrado y si lo está, reenvio el line (invite)
                if self.diccionario_user.has_key(nombre_usuario):
                    # con la dirección sip saco la ip y el puerto del diccionario.
                    uaip = self.diccionario_user[nombre_usuario][0]
                    print uaip
                    uaport = self.diccionario_user[nombre_usuario][2]
                    print uaport
                    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_socket.connect((uaip, int(uaport)))  
                    my_socket.send(line)
                    hora = time.time()
                    evento = " Sent to " + str(uaip) + str(uaport) + line + '\r\n'
                    log(hora, evento)
                    #Busco la ip origen
                    lista_split_ip = lista[4].split('\r\n')
                    lista_ip = lista_split_ip[0]
                    lista_split_sip = lista[1].split(":")
                    lista_nombre = lista_split_sip[1]
                    ip_receive = lista_ip
                    puerto_receive = self.diccionario_user[lista_nombre][2]
                    print "PUERTO"
                    print puerto_receive
                    evento = " Received to " + str(ip_receive) + " " + str(puerto_receive) + " " + line + '\r\n'
                    data = my_socket.recv(1024)
                    print " necesito sip para puerto"
                    print lista
                    print data
                    self.wfile.write(data)
                elif metodo == "BYE"
                else:
                    print "El usuario no está registrado"
                    self.wfile.write("SIP/2.0 404 User Not Found\r\n")
                    hora = time.time()
                    error = " SIP/2.0 404 User Not Found"
                    evento = " Sent to " + str(uaip) + " " + str(uaport) + error + '\r\n'
                    log(hora, evento)      
            elif not metodo in metodos:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            else:
                self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")
            self.register2file()
        

if __name__ == "__main__":
    serv = SocketServer.UDPServer((ipserver, int(portserver)), SIPRegisterHandler)
    print "Server " + usuario + " listening at port " + portserver + "..."
    serv.serve_forever()
