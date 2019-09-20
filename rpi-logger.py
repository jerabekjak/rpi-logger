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
        # set sep
        self._sep = ','
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
        # set header
        self._header = '{}{sep}{}{sep}{}'.format('TIMESTAMP','humid_proc','temp_c',sep=self._sep)

        ### SETUP PROBES ###
        # nastavi dht11
        self._humid = Humid(dht_pin)

    def _send_reading(self,line):
        # TODO  pridat line do mycmd
        mycmd = "ssh {} 'echo {} >> {}'".format(self._server, line, 
                self._remote_file)
        # print (mycmd)
        os.system(mycmd)

    def _make_header(self):
        # first line in the file is the header
        self._write_line(self._header)

    
    def _write_line(self,line):
        # write line in local and remote file
        self._send_reading(line)
        line += '\n'
        with open(self._logfile,'a') as f:
            f.write(line)


    def loop(self):
        """" logovaci smicka """

        self._make_header()

        while True:

            # make new line
            time = datetime.datetime.now()
            time = time.strftime('%Y-%m-%d %H:%M:00')
            line = '{}{sep}'.format(time,sep=self._sep)
            
            # nacte vlhkost a teploty z dht cidla
            ht = self._humid.read()
            
            # prida vlhost a teploty do line 
            line += '{}{sep}'.format(ht[0],sep=self._sep)
            line += '{}'.format(ht[1])
            
            self._write_line(line)


if __name__ == '__main__':

    logger = Logger(dht_pin=4, server='skola', 
            remote_dir='/home/jakub/public_html/rpidatapeklo/')
    logger.loop()

