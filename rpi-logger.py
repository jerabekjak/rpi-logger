#!/usr/bin/python
import os
import sys
import time 
import datetime


class Humid(object):
    def __init__(self,pin):
        import Adafruit_DHT as dht

        self._sensor = dht.DHT11
        self._pin = pin
        self._read = dht.read_retry

    def read(self):
        ht = self._read(self._sensor, self._pin)
        return (ht)


class Logger(object):
    """ Obstara vse okolo logovani """

    def __init__ (self, dht_pin, server, remote_dir):
        """ nastavy jednotliva cidla
        
        dht.pin: gpio na kterem je dht11
        """

        ### GENERAL SETTINGS ###
        # nastaveni pracovniho adresare
        self._root = os.path.dirname(os.path.abspath(__file__))
        # current time
        nf = datetime.datetime.now()
        # vytvoreni local souboru na logovani
        self._logfile = '{}/{}.dat'.format(self._root,nf.strftime('%Y%m%d%H%M'))
        # setup remote server
        self._server = server
        # setup remote soubor na logovani
        self._remote_file = '{}/{}.dat'.format(remote_dir,nf.strftime('%Y%m%d%H%M'))

        ### SETUP PROBES ###
        # nastavi dht11
        self._humid = Humid(dht_pin)

    def _send_reading(self,line):
        # TODO  pridat line do mycmd
        mycmd = "ssh {} 'echo {} >> {}'".format(self._server, line, 
                self._remote_file)
        # print (mycmd)
        os.system(mycmd)

    def loop(self):
        """" logovaci smicka """
        while True:

            # vynuluje line
            line = ''
            
            # nacte vlhkost a teploty z dht cidla
            ht = self._humid.read()
            
            # prida vlhost a teploty do line 
            line += str(ht[0]) + ' '
            line += str(ht[1])
            
            self._send_reading(line)
            line += '\n'
            print (line)

            # with open(self._logfile,'a') as f:
            #     f.write(line)


if __name__ == '__main__':

    logger = Logger(dht_pin=4, server='skola', 
            remote_dir='/home/jakub/public_html/rpidatapeklo/')
    logger.loop()

