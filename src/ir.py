from twisted.internet import reactor
from udpwkpf import WuClass, Device
import sys,time
from udpwkpf_io_interface import *
import requests
import json
myurl="http://10.1.2.23:3000/ir"

Pin1 = 2 # depends on which analog port
Pin2 = 5

class Ir(WuClass):
    def __init__(self):
        WuClass.__init__(self)
        self.loadClass('Ir')
        self.ir1_sensor_aio = pin_mode(Pin1, PIN_TYPE_ANALOG)
        self.ir2_sensor_aio = pin_mode(Pin2, PIN_TYPE_ANALOG)
        self.temp1 = 0
        self.temp2 = 0
        self.count = 8
        print "Ir sensor init!"

    def update(self,obj,pID=None,val=None):
        time.sleep(0.5)
        try:
            ir1 = analog_read(self.ir1_sensor_aio)
            obj.setProperty(0, ir1) 
            ir2 = analog_read(self.ir2_sensor_aio)
            obj.setProperty(0, ir2)
            print "Sound sensor analog pin: %d, value: %d" % (Pin1, ir1)
            print "Sound sensor analog pin: %d, value: %d" % (Pin2, ir2)

            if ir1 > 250:
                self.temp1 = ir1
            elif ir2 > 250:
                self.temp2 = ir2

            if self.temp1 > 250 and self.temp2 > 250:
                if self.temp1 > self.temp2:
                    print "get on"
                    if self.count > 0: 
                        self.count = self.count - 1
                elif self.temp1 < self.temp2:
                    print "get off"
                    if self.count < 8:
                        self.count = self.count+1 
                self.temp1 = 0
                self.temp2 = 0
            else:
                print "nobody"
                print "number of people=%d" %(self.count)    
        except IOError:
            print ("Error")

        people={"count":self.count}                        
        response = requests.post(myurl,json=people)

class MyDevice(Device):
    def __init__(self,addr,localaddr):
        Device.__init__(self,addr,localaddr)

    def init(self):
        self.m = Ir()
        self.addClass(self.m,0)
        self.obj_ir_sensor = self.addObject(self.m.ID)

if len(sys.argv) <= 2:
        print 'python %s <gip> <dip>:<port>' % sys.argv[0]
        print '      <gip>: IP addrees of gateway'
        print '      <dip>: IP address of Python device'
        print '      <port>: An unique port number'
        print ' ex. python %s 192.168.4.7 127.0.0.1:3000' % sys.argv[0]
        sys.exit(-1)

d = MyDevice(sys.argv[1],sys.argv[2])

reactor.run()

