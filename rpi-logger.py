#!/usr/bin/python

# TODO humidity probe reads None or two times 
#      smaller values if tempereture probe is 
#      on the same power wire (or there is other reason)
import os
import sys
import glob
import time 
import datetime

def wait_for_internet_connection():
    import urllib2
    while True:
        try:
            response = urllib2.urlopen('http://storm.fsv.cvut.cz',timeout=1)
            return
        except urllib2.URLError:
            pass

class Humid(object):
    def __init__(self,pin):
        import Adafruit_DHT as dht

        self._sensor = dht.DHT11
        self._pin = pin
        self._read = dht.read_retry

    def read(self):
        ht = self._read(self._sensor, self._pin)
        return (ht)


class Temp(object):

    def __init__(self):

        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
  
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')
        self._device_file = [df + '/w1_slave' for df in device_folder] 


    def _read_temp_raw(self,df):
      f = open(df, 'r')
      lines = f.readlines()
      f.close()
      return lines
                 
    def read(self):
        temp_c = []
        for idf in self._device_file :
            lines = self._read_temp_raw(idf)
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = read_temp_raw(idf)
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp = float(temp_string) / 1000.0
            temp_c.append(temp)
        return temp_c


class Logger(object):
    """ Obstara vse okolo logovani """

    def __init__ (self, dht_pin, server, remote_dir, sleep_sec):
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
        # setup remote dir
        self._remote_dir = remote_dir
        # setup remote soubor na logovan
        self._remote_file = '{}/{}.dat'.format(self._remote_dir,nf.strftime('%Y%m%d%H%M'))
        # set header
        self._header = '{}{sep}{}{sep}{}{sep}{}'.format('TIMESTAMP','humid_proc','temp_c','temp_c_outside',sep=self._sep)
        # set sleep time
        self._sleep_sec = sleep_sec

        ### SETUP PROBES ###
        self._humid = Humid(dht_pin)
        self._temp  = Temp()

    def _send_reading(self,line,file_,append=True):
        """ send line to remote server """
        if (append) :
            mycmd = "ssh {} 'echo {} >> {}'".format(self._server, line, 
                file_)
        else :
            mycmd = "ssh {} 'echo {} > {}'".format(self._server, line, 
                file_)

        os.system(mycmd)

    def _make_header(self):
        """ first line in the file is the header """
        self._write_line(self._header)
    
    def _write_line(self,line):
        """  write line in local and remote file """
        self._send_reading(line, self._remote_file)
        line += '\n'
        with open(self._logfile,'a') as f:
            f.write(line)

    def _write_current_reading(self,line):
        """write last reading to separate file"""
        # setup remote soubor 
        # local file 
        file_ = 'current_reading'
        remote_file = '{}/{}.dat'.format(self._remote_dir,file_)
        local_file = '{}/{}.dat'.format(self._root,file_)

        # send remote
        self._send_reading(self._header, remote_file, append=False)
        self._send_reading(line, remote_file, append=True)
        # save local
        with open(local_file,'w') as f:
            f.write(self._header+'\n')
            f.write(line)




    def loop(self):
        """" logovaci smicka """

        self._make_header()

        while True:

            # make new line
            time_ = datetime.datetime.now()
            time_ = time_.strftime('%Y-%m-%d %H:%M:%S')
            line = '{}{sep}'.format(time_,sep=self._sep)
            
            # nacte vlhkost a teploty z dht cidla
            ht = self._humid.read()
            t  = self._temp.read() 
            # prida vlhost a teploty do line 
            line += '{}{sep}'.format(ht[0],sep=self._sep)
            line += '{}{sep}'.format(ht[1],sep=self._sep)
            line += '{}'.format(t[0])
            
            self._write_line(line)
            self._write_current_reading(line)

            time.sleep(self._sleep_sec)


if __name__ == '__main__':

    # wait untill internet connection is active
    wait_for_internet_connection()
    # init logger
    logger = Logger(dht_pin=14, server='skola', 
            remote_dir='/home/jakub/public_html/rpidatapeklo/',
            sleep_sec = 1)
    logger.loop()

