#!/usr/bin/env python
import pigpio, time, crcmod.predefined, smbus, socket, sys
import atexit

def exit_handler(omron):
   omron.piGPIO.i2c_close(1)
   print "i2c has been closed"

class OmronD6T(object):
   def __init__(self, rasPiChannel=1, omronAddress=0x0a, arraySize=16):
      self.MAX_RETRIES = 5
      self.roomTemp = 0
      self.omronAddress = omronAddress
      self.arraySize = arraySize
      self.BUFFER_LENGTH=(arraySize * 2) + 3       # data buffer size 
      self.CRC_ERROR_BIT = 0x04                    # the third bit
      self.CRC = 0xa4 / (16/arraySize)                             # if you take the CRC of the whole word including the PEC, this is what you get
      self.piGPIO = pigpio.pi()
      self.piGPIOver = self.piGPIO.get_pigpio_version()
      self.i2cBus = smbus.SMBus(1)
      time.sleep(0.1)                # Wait
      
      # initialize the device based on Omron's appnote 1
      self.retries = 0
      self.result = 0
      for i in range(0,self.MAX_RETRIES):
         time.sleep(0.05)                               # Wait a short time
         self.handle = self.piGPIO.i2c_open(rasPiChannel, omronAddress) # open Omron D6T device at address 0x0a on bus 1
	 print self.handle
         if self.handle > 0:
            self.result = self.i2cBus.write_byte(self.omronAddress,0x4c)
            break
         else:
            print ''
            print '***** Omron init error ***** handle='+str(self.handle)+' retries='+str(self.retries)
            self.retries += 1
            
   # function to read the omron temperature array
   def read(self):
      self.temperature_data_raw=[0]*self.BUFFER_LENGTH
      self.temperature=[0.0]*self.arraySize         # holds the recently measured temperature
      self.values=[0]*self.BUFFER_LENGTH
      
      # read the temperature data stream - if errors, retry
      retries = 0
      for i in range(0,self.MAX_RETRIES):
         time.sleep(0.05)                               # Wait a short time
         (self.bytes_read, self.temperature_data_raw) = self.piGPIO.i2c_read_device(self.handle, self.BUFFER_LENGTH)
         print self.bytes_read       
         # Handle i2c error transmissions
         if self.bytes_read != self.BUFFER_LENGTH:
            print ''
            print '***** Omron Byte Count error ***** - bytes read: '+str(self.bytes_read)
            
            self.retries += 1                # start counting the number of times to retry the transmission

         if self.bytes_read == self.BUFFER_LENGTH:
            # good byte count, now check PEC
            
            t = (self.temperature_data_raw[1] << 8) | self.temperature_data_raw[0]
            self.tPATc = float(t)/10
            self.roomTemp = self.tPATc

            a = 0
            for i in range(2, len(self.temperature_data_raw)-2, 2):
               self.temperature[a] = float((self.temperature_data_raw[i+1] << 8) | self.temperature_data_raw[i])/10
               a += 1

            # Calculate the CRC error check code
            # PEC (packet error code) byte is appended at the end of each transaction. The byte is calculated as CRC-8 checksum, calculated over the entire message including the address and read/write bit. The polynomial used is x8+x2+x+1 (the CRC-8-ATM HEC algorithm, initialized to zero)
            self.crc8_func = crcmod.predefined.mkCrcFun('crc-8')
            
            for i in range(0,self.bytes_read):
               self.values[i] = self.temperature_data_raw[i]
                  
            self.string = "".join(chr(i) for i in self.values)
            self.crc = self.crc8_func(self.string)
               
            if self.crc != self.CRC:
               print '***** Omron CRC error ***** Expected '+'%02x'%self.CRC+' Calculated: '+'%02x'%self.crc
               self.retries += 1                # start counting the number of times to retry the transmission
               self.bytes_read = 0           # error is passed up using bytes read
            else:
               break    # crc is good and bytes_read is good

      return self.bytes_read, self.temperature

if __name__ == '__main__':
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.connect(('192.168.4.71', 9634))
   print 'connect'   
   omron = OmronD6T()
   atexit.register(exit_handler, omron)
   while True:
      start = time.time()
      omron.read()
      end = time.time()
      print "time taken: ",end-start
      #print "ICTemp:",omron.roomTemp
      #for i in range(0,len(omron.temperature)):
         #print "Cell",str(i)+":",omron.temperature[i]
      print "length: ", len(omron.temperature)
      print "type: ", type(omron.temperature)
      for i in range(4):
          print [omron.temperature[i*4 + j] for j in range(4)]
      s.send('{}, {},'.format(end - start, omron.temperature))
      print ''
      #time.sleep(0.15)
    
