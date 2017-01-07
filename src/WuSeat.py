import sys
from twisted.internet import reactor
from udpwkpf import WuClass, Device
import socket
import requests
import json
myurl="http://10.1.2.23:3000"

if __name__ == "__main__":
	class Thermal_sensor(WuClass):
		def __init__(self):
			WuClass.__init__(self)
			self.loadClass('SeatTable')

                        ##debug message
                        #self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        #self.s.connect(('10.1.2.13',9634))
		def update(self, obj, pID=None, val=None):
                        index1=obj.getProperty(0)
                        #index2=obj.getProperty(1)
                        tmp=[]
                        Sum = index1
                        for x in range(0,8):
                            tmp.append(Sum%2)
                            Sum=Sum/2
                        bit=list(reversed(tmp))
                        seatTable={"seat":bit}
                        print seatTable
                        response = requests.post(myurl,json=seatTable)

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
