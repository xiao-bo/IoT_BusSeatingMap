from OmGui_v4 import IRCameraData  # on computer
from Pi_Omrond6t import OmronD6T # on Pi
import sys
from twisted.internet import reactor
from udpwkpf import WuClass, Device
import time
import socket
from bitarray import bitarray

if __name__ == "__main__":
	class Thermal_sensor(WuClass):
		def __init__(self):
			WuClass.__init__(self)
			self.loadClass('Thermal_sensor')
			self.omron = OmronD6T()			# on Pi
			#self.processor = IRCameraData((0,0,400,400),(15,12,0,3))		# on computer

			#self.counter = 0
                        self.seat=bitarray('000000000000')

                        ##debug message
                        #self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        #self.s.connect(('10.1.2.13',9634))
		def update(self, obj, pID=None, val=None):
			self.get_data()
                        #obj.setProperty(0, message)
                        self.seat=bitarray('000000000000')
                        Threshold=obj.getProperty(1)
                        Threshold=28
                        if self.omron.temperature[10]>Threshold :
                            self.seat=self.seat | bitarray('100000000000')
                            print "1"
                        if self.omron.temperature[9]>Threshold:
                            self.seat=self.seat | bitarray('010000000000')
                            print "2"
                        if self.omron.temperature[6]>Threshold:
                            self.seat=self.seat | bitarray('001000000000')
                            print "3"
                        if self.omron.temperature[5]>Threshold:
                            self.seat=self.seat | bitarray('000100000000')
                            print "4"
                        #print self.seat

                        ## change bit into int
                        seatInt=0
                        for bit in self.seat:
                            seatInt = (seatInt<<1)|bit
                        ##
                        #print seatInt
                        obj.setProperty(0,seatInt)
		def get_data(self):

                        ## debug message
			#start=time.time()
                        ## debug 

                        self.omron.read()  			# on Pi
                        
                        ## debug message
                        #end=time.time()
                        #self.s.send('{},{},'.format(end-start,self.omron.temperature))
                        
                        ##debug message 
                        print self.omron.temperature
                        #print self.omron.temperature[0]

	class MyDevice(Device):
		def __init__(self, addr, localaddr):
			Device.__init__(self, addr, localaddr)

		def init(self):
			cls = Thermal_sensor()
			self.addClass(cls, 0)
			self.addObject(cls.ID)

	if len(sys.argv) <= 2:
		print 'python %s <gip> <dip>:<port>' % sys.argv[0]
		sys.exit(-1)

	d = MyDevice(sys.argv[1], sys.argv[2])
	reactor.run()
