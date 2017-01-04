from OmGui_v4 import IRCameraData  # on computer
from Pi_Omrond6t import OmronD6T # on Pi
import sys
from twisted.internet import reactor
from udpwkpf import WuClass, Device


if __name__ == "__main__":
	class OmronIRSensor(WuClass):
		def __init__(self):
			WuClass.__init__(self)
			self.loadClass('OmronIRSensor')
			self.omron = OmronD6T()			# on Pi
			self.processor = IRCameraData()		# on computer
			#self.counter = 0

		def update(self, obj, pID=None, val=None):
			self.get_data()
			message = '' + str(self.processor.roughDensity) + str(self.processor.currentAvgSpeed)
			obj.setProperty(0, message)
			#self.counter = (self.counter + 1) % 10

		def get_data(self):
			self.omron.read()  			# on Pi
			data_in = [0]
			data_in.extend(self.omron.temperature)
			self.processor.data = data_in		# on computer
			self.processor.calibrate_min_max()
			if self.processor.foreignObject.__len__() == 0:
				self.processor.past_frame_sample_mean()
			self.processor.foreign_object_detection()
			try:  # TODO fix this, error when attempting to process multiple people
				self.processor.route()
			except IndexError:
				pass

	class MyDevice(Device):
		def __init__(self, addr, localaddr):
			Device.__init__(self, addr, localaddr)

		def init(self):
			cls = OmronIRSensor()
			self.addClass(cls, 0)
			self.addObject(cls.ID)

	if len(sys.argv) <= 2:
		print 'python %s <gip> <dip>:<port>' % sys.argv[0]
		sys.exit(-1)

	d = MyDevice(sys.argv[1], sys.argv[2])
	reactor.run()
