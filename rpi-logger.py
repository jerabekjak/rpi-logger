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

    def __init__ (self, dht_pin):
        """ nastavy jednotliva cidla
        
        dht.pin: gpio na kterem je dht11
        """

        # nastaveni adresare na ulozeni dat 
        self._root = '/home/pi/rpi-project/home-logger/'
        self._root = os.path.dirname(os.path.abspath(__file__))
        print ('working directory in {}'.format(self._root))

        # vytvoreni souboru na logovani
        nf = datetime.datetime.now()
        self._logfile = '{}/{}.dat'.format(self._root,nf.strftime('%Y%m%d%H%M'))
        
        # nastavi dht11
        self._humid = Humid(dht_pin)

    def _send_reading(self,line):
        # TODO  pridat line do mycmd
        mycmd = "ssh skola 'echo tesasdfasdft >> /home/jakub/public_html/test'"
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
            
            line += '\n'
            with open(self._logfile,'a') as f:
                f.write(line)


if __name__ == '__main__':

    logger = Logger(4)
    logger.loop()

