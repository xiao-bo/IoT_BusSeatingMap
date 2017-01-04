import cProfile
import math
import pygame
import re
import socket
import time
import collections

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 4.33
# 4.129
# 4.103
# 4.57
windowSize = 400
cellSize = windowSize / 4

touch_check = [[1, 4], [0, 2, 5], [1, 3, 6], [2, 7], [0, 5, 8], [1, 4, 6, 9], [2, 5, 7, 10], [3, 6, 11], [4, 9, 12],
			   [5, 8, 10, 13], [6, 9, 11, 14], [7, 10, 15], [8, 13], [9, 12, 14], [10, 13, 15], [11, 14]]


class IRCameraData:
	def __init__(self, (x_min, y_min, x_max, y_max), (top_left, top_right, bot_right, bot_left)):
		self.xPos = []
		self.yPos = []
		self.xCenter = []
		self.yCenter = []
		self.define_drawing_area(x_min, y_min, x_max, y_max, top_left, top_right, bot_right, bot_left)
		self.xSize = x_max - x_min
		self.ySize = y_max - y_min

		self.data = []

		self.points = [(0, 0, 255), (0, 255, 255), (0, 255, 0), (255, 255, 0), (255, 0, 0)]
		self.globalMaxTemp = 35.0
		self.globalMinTemp = 20.0
		self.globalTempRange = self.globalMaxTemp - self.globalMinTemp
		self.minMean = 999
		self.maxMean = -999
		self.pastMin = []
		self.pastMax = []

		self.frameAccepted = []
		self.frameCount = 0
		self.frameTiming = []
		self.timingSum = 0
		self.totalTime = 0

		self.lastFrame = []
		self.prevFrames = []
		self.sampleSize = 150
		self.sampleMean = []
		self.prevForeignObject = []
		self.foreignObject = []
		self.threshold = 1
		self.needUpdate = 0
               
		self.foreignObjectPath = []
		self.uniqueForeignObjects = []
		self.done = 1

		self.pointTiming = []
		self.pointSpeed = []
		self.roughDensity = 0
		self.currentAvgSpeed = 0

	# sets up the pos and centers, based on min max and rotations
	def define_drawing_area(self, x_min, y_min, x_max, y_max, top_left, top_right, bot_right, bot_left):
		rota = []
		for x in range(0, 16):
			self.xPos.append(0)
			self.yPos.append(0)
			self.xCenter.append(0)
			self.yCenter.append(0)
			rota.append(0)
		rota[0] = bot_left #3
		rota[3] = top_left #15
		rota[12] = bot_right #0
		rota[15] = top_right #12
		rota[4] = rota[0] + (rota[12] - rota[0]) / 3 #3+(-1) = 2
		rota[8] = rota[4] + (rota[12] - rota[0]) / 3 #2+(-1) = 1
		rota[7] = rota[3] + (rota[15] - rota[3]) / 3 #15+(-1) = 14
		rota[11] = rota[7] + (rota[15] - rota[3]) / 3#14+(-1) = 13
		for x in range(1, 14, 4):
			for y in range(0, 2):
				rota[x + y] = rota[x + y - 1] + (rota[x + 2] - rota[x - 1]) / 3
		x_size = (x_max - x_min) / 4
		y_size = (y_max - y_min) / 4
		for x in range(0, 4):
			for y in range(0, 4):
				self.xPos[rota[x * 4 + y]] = x_min + x_size * (x)
				self.yPos[rota[x * 4 + y]] = y_min + y_size * (3-y)
		for x in range(0, 16):
			self.xCenter[x] = self.xPos[x] + x_size / 2
			self.yCenter[x] = self.yPos[x] + y_size / 2

	# only start looking for foreign object after mean has 30 samples, difference between mean
	def foreign_object_detection(self):
		self.foreignObject = []
		if self.sampleSize >= 30:
			for x in range(0, 16):
				if abs(self.data[x + 1] - self.sampleMean[x]) > self.threshold:
					self.foreignObject.append(x)
		if self.foreignObject.__len__() != 0:  # if found foreign
			if self.prevForeignObject.__len__() == 0 or self.prevForeignObject != self.foreignObject:  # if unique or empty
				self.prevForeignObject = self.foreignObject
				self.uniqueForeignObjects.append(self.foreignObject)
				self.needUpdate = 1
		else:
			self.uniqueForeignObjects = []

	# if unique objects set is not empty and set has changed
	# 	<process all disconnected sets>
	# 	<map each new point to a prev path>
	# elif obj left, reset

	#       <process all disconnected sets> 
	# 	if fop is empty, add all
	# 	else
	# 		if fop.len < cl.len
	# 			add cl to closest fop[x][last]
	# 			split case, create new entry with single element fop[x][last] before adding cl[x]
	# 		else	(fop.len >= cl.len)
	# 			add cl to closest fop[x][last]
	# 			delete fop[not added to]
	def route(self):
		if self.uniqueForeignObjects.__len__() != 0 and self.needUpdate:
			self.rough_density()
			self.done = 0
			self.needUpdate = 0
			cur_loc = []
			analyze = list(self.uniqueForeignObjects[-1])
                        print "analyze: ", analyze
			while analyze.__len__() != 0:
				(out_x, out_y, out_size) = self.calculate_center(analyze[0], analyze)
				cur_loc.append([out_x / out_size, out_y / out_size])
			print 'cur_loc: ', cur_loc
			if self.foreignObjectPath.__len__() == 0:
                                for i in range(cur_loc.__len__()):
                                        init_path = collections.deque(maxlen=5)
                                        init_path.append(cur_loc[i])
				        self.foreignObjectPath.append(init_path)
				        self.pointTiming.append([time.time()])
				        self.pointSpeed.append([0])
			else:
				if self.foreignObjectPath.__len__() < cur_loc.__len__():
	                                # add cl to closest fop[x][last]
					tmp_fop = []
					use_set = []
					for x in range(0, self.foreignObjectPath.__len__()):
	                                        # create new entry with single element fop[x][last] before adding cl[x]
						tmp_fop.append(self.foreignObjectPath[x][-1])
						use_set.append(x)
					for x in range(0, cur_loc.__len__()):
						min_val = distance_from((tmp_fop[0][0], tmp_fop[0][1]), (cur_loc[x][0], cur_loc[x][1]))
						min_index = 0
						if self.foreignObjectPath.__len__() > 1:
							for y in range(1, self.foreignObjectPath.__len__()):
								cur_dis = distance_from((cur_loc[x][0], cur_loc[x][1]), (tmp_fop[y][0], tmp_fop[y][1]))
								if cur_dis < min_val:
									min_val = cur_dis
									min_index = y
						if min_val < 2 * cellSize:
							if use_set.__contains__(min_index):
								self.foreignObjectPath[min_index].append(cur_loc[x])
								use_set.remove(min_index)
							else:
                                                                new_path = collections.deque(maxlen=5)
                                                                new_path.append(tmp_fop[min_index])
                                                                new_path.append(cur_loc[x])
								self.foreignObjectPath.append(new_path)
                                                                tmp_fop.append(cur_loc[x])
								self.pointTiming.append([time.time()])
								self.pointSpeed.append([0])
						else:
                                                        new_path = collections.deque(maxlen=5)
                                                        new_path.append(cur_loc[x])
							self.foreignObjectPath.append(new_path)
                                                        tmp_fop.append(cur_loc[x])
							self.pointTiming.append([time.time()])
							self.pointSpeed.append([0])
				else:
					use_set = []
					for x in range(0, self.foreignObjectPath.__len__()):
						use_set.append(x)
					for x in range(0, cur_loc.__len__()):
	                                        # add cl to closest fop[x][last]
						min_val = distance_from((cur_loc[x][0], cur_loc[x][1]),
												(self.foreignObjectPath[use_set[0]][-1][0],
												 self.foreignObjectPath[use_set[0]][-1][1]))
              					min_index = 0
						if use_set.__len__() > 1:
							for y in range(1, use_set.__len__()):
								cur_dis = distance_from((cur_loc[x][0], cur_loc[x][1]), (
									self.foreignObjectPath[use_set[y]][-1][0],
									self.foreignObjectPath[use_set[y]][-1][1]))
								if cur_dis < min_val:
									min_val = cur_dis
									min_index = y
						self.foreignObjectPath[use_set[min_index]].append(cur_loc[x])
						self.pointTiming[use_set[min_index]].append(time.time())
						self.pointSpeed[use_set[min_index]].append(self.calc_speed(use_set[min_index]))
						del use_set[min_index]
					for x in reversed(range(0, use_set.__len__())):
	                                        # delete fop[not added to]
						self.calc_avg_speed(use_set[x])
                                                print "x: ", x
                                                print "self.foreignObjectPath: ", self.foreignObjectPath
						del self.foreignObjectPath[use_set[x]]
		elif self.uniqueForeignObjects.__len__() == 0:  # object left
			if not self.done:
				for x in range(0, self.pointSpeed.__len__()):
					self.calc_avg_speed(x)
				self.done = 1
				self.pointSpeed = []
				self.pointTiming = []
				self.foreignObjectPath = []
				self.roughDensity = 0
				self.currentAvgSpeed = 0

	# calculates the speed
	def calc_speed(self, x_index):
		out = distance_from(self.foreignObjectPath[x_index][-1], self.foreignObjectPath[x_index][-2]) / (
			self.pointTiming[x_index][-1] - self.pointTiming[x_index][-2] + 0.1)
		self.calc_avg_speed(x_index)
		return out

	# calculates the avg speed
	def calc_avg_speed(self, x_index):
		avg_spd = 0
		for y in range(0, self.pointSpeed[x_index].__len__()):
			avg_spd += self.pointSpeed[x_index][y]
		if self.pointSpeed[x_index].__len__() == 1:
			self.currentAvgSpeed = avg_spd
		if self.pointSpeed[x_index].__len__() > 1:
			self.set_avg_spd(avg_spd / (self.pointSpeed[x_index].__len__() - 1)) 
                        # self.pointSpeed[0] is zero; thus, we have to decrease 1

	# normalizes avg spd
	def set_avg_spd(self, new_val):
		self.currentAvgSpeed = int(new_val) / 45
		self.currentAvgSpeed = self.currentAvgSpeed % 10

	# check how many sensors are lit up
	def rough_density(self):
		cur = self.uniqueForeignObjects[-1].__len__()
		if cur == 0:
			self.roughDensity = 0
		elif cur < 6:
			self.roughDensity = 1
		else:
			self.roughDensity = 2
		print "self.roughDensity: ", self.roughDensity
		
	# check if cells start and end are connected, no diag
	def check_connect(self, start, end, check_list):
		if start == end:
			return 1
		if touch_check[start].__contains__(end):
			return 1
		next_pass = list(check_list)
		try:
			next_pass.remove(start)
		except ValueError:
			pass
		for x in range(0, touch_check[start].__len__()):
			if check_list.__contains__(touch_check[start][x]):
				if self.check_connect(touch_check[start][x], end, next_pass):
					return 1
                return 0

	# calculate the center for group of adjacent cells containing the cell start
	# will remove processed cells from original list passed in
	def calculate_center(self, start, check_list):
		out_x = self.xCenter[start]
		out_y = self.yCenter[start]
		out_size = 1
		check_list.remove(start)
		x = 0
		cur_group = [start]
		while x < check_list.__len__():
			for y in range(0, cur_group.__len__()):
				if self.check_connect(cur_group[y], check_list[x], check_list):
                                        cur_group.append(check_list[x])
					out_x += self.xCenter[check_list[x]]
					out_y += self.yCenter[check_list[x]]
					out_size += 1
					check_list.remove(check_list[x])
					x -= 1
					break
			x += 1
		return out_x, out_y, out_size

	# calculates a mean with the 150 most recent frame data
	# only called when no FO in frame to try to limit mean sample to background only
	def past_frame_sample_mean(self):
		self.prevFrames.append(self.data[1:17])  # add current frame to list of frame
		self.lastFrame = []
		for x in range(1, 17):
			self.lastFrame.append(self.data[x])
		if self.prevFrames.__len__() > self.sampleSize:  # too many sample, trim, regular case after starting
			delete_set = self.prevFrames.pop(0)
			for x in range(0, 16):
				self.sampleMean[x] -= (delete_set[x] / self.prevFrames.__len__())
				self.sampleMean[x] += (self.lastFrame[x] / self.prevFrames.__len__())
		elif self.sampleMean.__len__() == 0:  # first frame received
			for x in range(0, 16):
				self.sampleMean.append(self.data[x + 1])
		else:  # before reaching the sample size
			for x in range(0, 16):
				self.sampleMean[x] = (self.sampleMean[x] * (self.prevFrames.__len__() - 1) + self.lastFrame[
					x]) / self.prevFrames.__len__()

	# calculate the fps, doesnt work with MultiRon, maybe because threading
	def frame_counting(self, start_time, dropped):
		if __name__ == "__main__":
			time_taken = time.time() - start_time
			self.frameTiming.append(time_taken)
			self.frameAccepted.append(dropped)
			self.frameCount += dropped
			self.timingSum += time_taken
			self.totalTime += time_taken
			while self.timingSum > 1:
				self.frameCount -= self.frameAccepted.pop(0)
				self.timingSum -= self.frameTiming.pop(0)

	# takes care of min max
	def calibrate_min_max(self):
		local_min = self.data[1]
		local_max = self.data[1]
		for x in range(2, 17):
			if self.data[x] > local_max:
				local_max = self.data[x]
			if self.data[x] < local_min:
				local_min = self.data[x]
		self.pastMin.append(local_min)
		self.pastMax.append(local_max)
		if self.pastMin.__len__() == 0:
			self.minMean = local_min
			self.maxMean = local_max
		elif self.pastMin.__len__() > self.sampleSize:
			self.minMean = (sum(self.pastMin) - self.pastMin.pop(0)) / self.pastMin.__len__()
			self.maxMean = (sum(self.pastMax) - self.pastMax.pop(0)) / self.pastMax.__len__()
		else:
			self.minMean = sum(self.pastMin) / self.pastMin.__len__()
			self.maxMean = sum(self.pastMax) / self.pastMax.__len__()
		if local_min < self.globalMinTemp:
			self.globalMinTemp = local_min
		elif abs(self.globalMinTemp - self.minMean) > abs(local_min - self.minMean):
			self.globalMinTemp += (abs(self.globalMinTemp - self.minMean) - abs(local_min - self.minMean)) * 0.2
		if local_max > self.globalMaxTemp:
			self.globalMaxTemp = local_max
		self.globalTempRange = self.globalMaxTemp - self.globalMinTemp

	# linear interpolation of temp value into a color from points rgb array
	def interpolate_color(self, value):
		ratio = ((value - self.globalMinTemp) / self.globalTempRange) * (self.points.__len__() - 1)
		ratio_floor = int(math.floor(ratio))
		ratio_ceil = int(math.ceil(ratio))
		if ratio_ceil == ratio_floor:
			r = self.points[ratio_ceil][0]
			g = self.points[ratio_ceil][1]
			b = self.points[ratio_ceil][2]
		else:
			g = self.points[ratio_floor][1] * (ratio - ratio_floor) + self.points[ratio_ceil][1] * (ratio_ceil - ratio)
			r = self.points[ratio_floor][0] * (ratio - ratio_floor) + self.points[ratio_ceil][0] * (ratio_ceil - ratio)
			b = self.points[ratio_floor][2] * (ratio - ratio_floor) + self.points[ratio_ceil][2] * (ratio_ceil - ratio)
		return int(r), int(g), int(b)


def distance_from((x1, y1), (x2, y2)):
	return math.sqrt(math.pow(abs(x1 - x2), 2) + math.pow(abs(y1 - y2), 2))


# all pygame related things except event handling
def draw_components(cam_data, _font, _surface):
	for x in range(0, 16):
		cell_color = cam_data.interpolate_color(cam_data.data[x + 1])
		pygame.draw.rect(_surface, cell_color, (cam_data.xPos[x], cam_data.yPos[x], cellSize, cellSize))
		ren = _font.render(str(cam_data.data[x + 1]), 0, (0, 0, 0))
		_surface.blit(ren, (cam_data.xPos[x], cam_data.yPos[x]))
	ren = _font.render(str(cam_data.frameCount), 0, (0, 0, 0))
	if __name__ == "__main__":
		_surface.blit(ren, (windowSize - 60, 60))
	for x in range(0, cam_data.foreignObjectPath.__len__()):
		y = cam_data.foreignObjectPath[x].__len__()
		pygame.draw.circle(_surface, (0, 0, 0), cam_data.foreignObjectPath[x][y-1], 10)
		#for y in range(0, cam_data.foreignObjectPath[x].__len__()):
		#	pygame.draw.circle(_surface, (0, 0, 0), cam_data.foreignObjectPath[x][y], 10)
		#	if y != 0:
		#		pygame.draw.line(_surface, (0, 0, 0), cam_data.foreignObjectPath[x][y - 1],
		#						 cam_data.foreignObjectPath[x][y])
	pygame.display.update()


# kinda un-break the incoming data then runs through all the IRCameraData methods
def data_processing(cam_data, data_in, _font, _surface, start_time):
	# if __name__ == "__main__":
	# 	if int(cam_data.totalTime) % 60 == 0:
	# 		print cam_data.totalTime
	if not data_in:
		return 0
	data_in = data_in.replace('[', '').replace(']', '')
	if data_in[0] == ',':
		data_in = data_in[1:]
	data_in = data_in.split(',')
	try:
		if data_in.__len__() != 18 and (
					re.search('[0-9]+\.[0-9]+', data_in[0].strip()) is None):
			# print 'cont', data_in.__len__(), data_in
			cam_data.frame_counting(start_time, 0)
			return 1
		for x in range(0, 17):
			data_in[x] = float(data_in[x])
	except ValueError:
		cam_data.frame_counting(start_time, 0)
		return 1
	except IndexError:
		cam_data.frame_counting(start_time, 0)
		return 1
	cam_data.data = data_in
	cam_data.calibrate_min_max()
	if cam_data.foreignObject.__len__() == 0:
		cam_data.past_frame_sample_mean()
	cam_data.foreign_object_detection()
	cam_data.route()
        for i in range(cam_data.foreignObjectPath.__len__()):
	    print "PATH %d: %s" % (i, str(cam_data.foreignObjectPath[i]))
	draw_components(cam_data, _font, _surface)
	cam_data.frame_counting(start_time, 1)
	return 1


# if main it will run single sensor
# run with MultiRon for 4(+?) sensor at once
if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('10.88.10.243', 9634))
	s.listen(1)
	conn, addr = s.accept()
	print 'Connection address', addr

	pygame.init()
	font = pygame.font.Font(None, 40)
	surface = pygame.display.set_mode((windowSize, windowSize))

	sensor = IRCameraData((0, 0, 400, 400), (15,12, 0, 3))
	#sensor = IRCameraData((0, 0, 400, 400), (15, 3, 0, 12))

	run = True
	pr = cProfile.Profile()
	pr.enable()
	while run:  # continue and break, next loop and return
		starting_time = time.time()
		data = conn.recv(1024)
		if not data_processing(sensor, data, font, surface, starting_time):
			break
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
	pr.disable()
	pr.print_stats(sort="tottime")
	conn.close()
