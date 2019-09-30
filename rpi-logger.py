#!/usr/bin/python

# TODO humidity probe reads None or two times 
#      smaller values if tempereture probe is 
#      on the same power wire (or there is other reason)
import os
import sys
import glob
import time 
import datetime
import smbus
from ctypes import c_short
from ctypes import c_byte
from ctypes import c_ubyte

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

class BME280(object):
    """
    #--------------------------------------
    #    ___  ___  _ ____
    #   / _ \/ _ \(_) __/__  __ __
    #  / , _/ ___/ /\ \/ _ \/ // /
    # /_/|_/_/  /_/___/ .__/\_, /
    #                /_/   /___/
    #
    #           bme280.py
    #  Read data from a digital pressure sensor.
    #
    #  Official datasheet available from :
    #  https://www.bosch-sensortec.com/bst/products/all_products/bme280
    #
    # Author : Matt Hawkins
    # Date   : 21/01/2018
    #
    # https://www.raspberrypi-spy.co.uk/
    #
    #--------------------------------------
    """
    def __init__(self):
        self._DEVICE = 0x76 # Default device I2C address
        self._bus = smbus.SMBus(1) # Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
                                   # Rev 1 Pi uses bus 0

    def _getShort(self,data, index):
        # return two bytes from data as a signed 16-bit value
        return c_short((data[index+1] << 8) + data[index]).value

    def _getUShort(self,data, index):
        # return two bytes from data as an unsigned 16-bit value
        return (data[index+1] << 8) + data[index]

    def _getChar(self,data,index):
        # return one byte from data as a signed char
        result = data[index]
        if result > 127:
              result -= 256
        return result

    def _getUChar(self,data,index):
        # return one byte from data as an unsigned char
        result =  data[index] & 0xFF
        return result

    def _readBME280ID(self):
        # Chip ID Register Address
        addr = self._DEVICE
        REG_ID     = 0xD0
        (chip_id, chip_version) = self._bus.read_i2c_block_data(addr, REG_ID, 2)
        return (chip_id, chip_version)

    def readBME280All(self):
        # Register Addresses
        addr = self._DEVICE
        REG_DATA = 0xF7
        REG_CONTROL = 0xF4
        REG_CONFIG  = 0xF5

        REG_CONTROL_HUM = 0xF2
        REG_HUM_MSB = 0xFD
        REG_HUM_LSB = 0xFE

        # Oversample setting - page 27
        OVERSAMPLE_TEMP = 2
        OVERSAMPLE_PRES = 2
        MODE = 1

        # Oversample setting for humidity register - page 26
        OVERSAMPLE_HUM = 2
        self._bus.write_byte_data(addr, REG_CONTROL_HUM, OVERSAMPLE_HUM)

        control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
        self._bus.write_byte_data(addr, REG_CONTROL, control)

        # Read blocks of calibration data from EEPROM
        # See Page 22 data sheet
        cal1 = self._bus.read_i2c_block_data(addr, 0x88, 24)
        cal2 = self._bus.read_i2c_block_data(addr, 0xA1, 1)
        cal3 = self._bus.read_i2c_block_data(addr, 0xE1, 7)

        # Convert byte data to word values
        dig_T1 = self._getUShort(cal1, 0)
        dig_T2 = self._getShort(cal1, 2)
        dig_T3 = self._getShort(cal1, 4)

        dig_P1 = self._getUShort(cal1, 6)
        dig_P2 = self._getShort(cal1, 8)
        dig_P3 = self._getShort(cal1, 10)
        dig_P4 = self._getShort(cal1, 12)
        dig_P5 = self._getShort(cal1, 14)
        dig_P6 = self._getShort(cal1, 16)
        dig_P7 = self._getShort(cal1, 18)
        dig_P8 = self._getShort(cal1, 20)
        dig_P9 = self._getShort(cal1, 22)

        dig_H1 = self._getUChar(cal2, 0)
        dig_H2 = self._getShort(cal3, 0)
        dig_H3 = self._getUChar(cal3, 2)

        dig_H4 = self._getChar(cal3, 3)
        dig_H4 = (dig_H4 << 24) >> 20
        dig_H4 = dig_H4 | (self._getChar(cal3, 4) & 0x0F)

        dig_H5 = self._getChar(cal3, 5)
        dig_H5 = (dig_H5 << 24) >> 20
        dig_H5 = dig_H5 | (self._getUChar(cal3, 4) >> 4 & 0x0F)

        dig_H6 = self._getChar(cal3, 6)

        # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
        wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
        time.sleep(wait_time/1000)  # Wait the required time  

        # Read temperature/pressure/humidity
        data = self._bus.read_i2c_block_data(addr, REG_DATA, 8)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]

        #Refine temperature
        var1 = ((((temp_raw>>3)-(dig_T1<<1)))*(dig_T2)) >> 11
        var2 = (((((temp_raw>>4) - (dig_T1)) * ((temp_raw>>4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
        t_fine = var1+var2
        temperature = float(((t_fine * 5) + 128) >> 8);

        # Refine pressure and adjust for temperature
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * dig_P6 / 32768.0
        var2 = var2 + var1 * dig_P5 * 2.0
        var2 = var2 / 4.0 + dig_P4 * 65536.0
        var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * dig_P1
        if var1 == 0:
            pressure=0
        else:
            pressure = 1048576.0 - pres_raw
            pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
            var1 = dig_P9 * pressure * pressure / 2147483648.0
            var2 = pressure * dig_P8 / 32768.0
            pressure = pressure + (var1 + var2 + dig_P7) / 16.0

        # Refine humidity
        humidity = t_fine - 76800.0
        humidity = (hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
        humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
        if humidity > 100:
            humidity = 100
        elif humidity < 0:
            humidity = 0

        return temperature/100.0,pressure/100.0,humidity

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
        self._header = '{}{sep}{}{sep}{}{sep}{}{sep}{}'.format('TIMESTAMP','humid_proc','temp_c','humid_proc','temp_c',sep=self._sep)
        # set sleep time
        self._sleep_sec = sleep_sec

        ### SETUP PROBES ###
        self._humid_1 = Humid(dht_pin[0])
        self._humid_2 = Humid(dht_pin[1])

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
            ht1 = self._humid_1.read()
            ht2 = self._humid_2.read()
            # prida vlhost a teploty do line 
            line += '{}{sep}'.format(ht1[0],sep=self._sep)
            line += '{}{sep}'.format(ht1[1],sep=self._sep)
            line += '{}{sep}'.format(ht2[0],sep=self._sep)
            line += '{}'.format(ht2[1])
            
            self._write_line(line)
            self._write_current_reading(line)

            time.sleep(self._sleep_sec)


if __name__ == '__main__':

    # wait untill internet connection is active
    wait_for_internet_connection()
    # init logger
    logger = Logger(dht_pin=[4,14], server='storm', 
            remote_dir='/home/jerabek/public_html/rpidatadoma/',
            sleep_sec = 1)
    logger.loop()

