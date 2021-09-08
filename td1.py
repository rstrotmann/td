#!/usr/local/bin/python3

import cairo
import json
import random


#############################
#	trial period class
#############################

class Periodelement(object):
	def __init__(self, period_dict=dict(), length=0, xoffset=10, yoffset=10, dayheight=20, daywidth=15, ypadding=7, debug=False):
		self._period_dict = period_dict
		self._xoffset = xoffset
		self._yoffset = yoffset
		self._dayheight = dayheight
		self._daywidth = daywidth
		self._ypadding = ypadding
		self._debug = debug
		self._length = length #self._period_dict["length"]

	def height(self, canvas):
		return 0

	@property
	def width(self):
		return self._length * self._daywidth

	def draw_dummy(self, canvas, yoffset, height=2):
		canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
		canvas.rectangle(self._xoffset, yoffset, self.width, height)
		canvas.fill()



class Procedure(Periodelement):
	def __init__(self, type="adminisitration", **kwargs):
		self._type = type
		Periodelement.__init__(self, **kwargs)

	def _metrics(self, canvas):
		caption = self._period_dict["caption"]
		(cap_x, cap_y, cap_width, cap_height, dx, dy) = canvas.text_extents(caption)
		return(caption, cap_width, cap_height)		

	def height(self, canvas):
		return self._metrics(canvas)[2] + 2 * self._ypadding

	def draw_dummy(self, canvas, yoffset):
		Periodelement.draw_dummy(self, canvas, yoffset=yoffset, height=self.height(canvas))

	def draw(self, canvas, yoffset, periodspacing=0):
		if self._debug:
			self.draw_dummy(canvas, yoffset=yoffset)
		(caption, cap_width, cap_height) = self._metrics(canvas)
		canvas.set_source_rgb(0, 0, 0)
		canvas.move_to(self._xoffset + self.width/2 - cap_width/2, yoffset + cap_height + self._ypadding)
		canvas.show_text(caption)		



class Periodcaption(Periodelement):
	def __init__(self, ypadding=5, **kwargs):
		Periodelement.__init__(self, **kwargs)

	def _metrics(self, canvas):
		caption = self._period_dict["caption"]
		(cap_x, cap_y, cap_width, cap_height, dx, dy) = canvas.text_extents(caption)
		return(caption, cap_width, cap_height)		

	def height(self, canvas):
		return self._metrics(canvas)[2] + 2 * self._ypadding

	def draw_dummy(self, canvas, yoffset):
		Periodelement.draw_dummy(self, canvas, yoffset=yoffset, height=self.height(canvas))

	def draw(self, canvas, yoffset):
		if self._debug:
			self.draw_dummy(canvas, yoffset)
		(caption, cap_width, cap_height) = self._metrics(canvas)
		canvas.set_source_rgb(0, 0, 0)
		canvas.move_to(self._xoffset + self.width/2 - cap_width/2, yoffset + cap_height + self._ypadding)
		canvas.show_text(caption)		



class Periodbox(Periodelement):
	def __init__(self, ypadding=0, **kwargs):
		Periodelement.__init__(self, ypadding=ypadding, **kwargs)

	def height(self, canvas):
		return self._dayheight + 2 * self._ypadding

	def draw_outline(self, canvas, yoffset):
		canvas.set_line_width(1)
		canvas.set_source_rgb(0, 0, 0)
		canvas.rectangle(self._xoffset, yoffset + self._ypadding, self.width, self._dayheight)
		canvas.stroke()

	def draw_dummy(self, canvas, yoffset):
		Periodelement.draw_dummy(self, canvas, yoffset=yoffset, height=self.height(canvas))

	def draw(self, canvas, yoffset, periodspacing=0):
		if self._debug:
			self.draw_dummy(canvas, yoffset)
		x = self._xoffset
		y = yoffset + self._ypadding
		for i in range(1, self._period_dict["length"]+1):
			canvas.set_line_width(1)
			canvas.set_source_rgb(0, 0, 0)
			canvas.rectangle(x, y, self._daywidth, self._dayheight)
			canvas.stroke()
			x += self._daywidth
		self.draw_outline(canvas, yoffset=yoffset)

		if periodspacing != 0:
			canvas.move_to(self._xoffset + self.width, yoffset + self._ypadding + self._dayheight/2)
			canvas.line_to(self._xoffset + self.width + periodspacing, yoffset + self._ypadding + self._dayheight/2)
			canvas.stroke()
		return 



class Period(object):
	def __init__(self, period_dict=dict(), daywidth=15, dayheight=20, xoffset=10, yoffset=10, periodspacing=15, debug=False):
		self._period_dict = period_dict
		self._daywidth = daywidth
		self._dayheight = dayheight
		self._xoffset = xoffset
		self._yoffset = yoffset
		self._periodspacing = periodspacing
		self._debug = debug
		self._length = period_dict["length"]

		self._periodcaption = Periodcaption(period_dict=period_dict, length=self._length, daywidth=daywidth, dayheight=dayheight, xoffset=xoffset, yoffset=yoffset, debug=self._debug)
		self._periodbox = Periodbox(period_dict=period_dict, length=self._length, daywidth=daywidth, dayheight=dayheight, xoffset=xoffset, yoffset=yoffset, debug=self._debug)

		self._elements = []
		# add further elements
		for a in self._period_dict["administrations"]:
			#print(a["caption"])
			self._elements.append(Procedure(type="administration", period_dict=a, length=self._length, daywidth=daywidth, dayheight=dayheight, xoffset=xoffset, yoffset=yoffset, debug=self._debug))
		for p in self._period_dict["procedures"]:
			#print(p["caption"])
			self._elements.append(Procedure(type=p["caption"], period_dict=p, length=self._length, daywidth=self._daywidth, dayheight=self._dayheight, xoffset=self._xoffset, yoffset=self._yoffset, debug=self._debug))

	def dump(self):
		print(json.dumps(self._period_dict, indent=2))

	def draw(self, canvas):
		y = self._yoffset
		self._periodcaption.draw(canvas, y)
		y += self._periodcaption.height(canvas)
		#self._periodbox._yoffset = self._periodcaption._yoffset + self._periodcaption.height(canvas)
		self._periodbox.draw(canvas, yoffset=y, periodspacing=self._periodspacing)
		y += self._periodbox.height(canvas)

		for e in self._elements:
			e.draw(canvas, yoffset=y, periodspacing=self._periodspacing)
			y += e.height(canvas)

	@property
	def width(self):
		return self._periodbox.width

	@property
	def xoffset(self):
		return self._xoffset

	@xoffset.setter
	def xoffset(self, value):
		self._xoffset = value
		self._periodbox._xoffset = value
		self._periodcaption._xoffset = value
		for e in self._elements:
			e._xoffset = value

	
	


#############################
#	trial design class
#############################

class Trialdesign(object):
	def __init__(self, js=dict(), xoffset=10, yoffset=10, periodspacing=15):
		self._period_dict = js
		self._xoffset = xoffset
		self._yoffset = yoffset
		self._periodspacing = periodspacing
		self._periods = []

		x = self._xoffset
		pp = self._period_dict["periods"]
		for p in pp:
			temp = Period(p, debug=True, periodspacing=self._periodspacing * (not p is pp[-1]))
			temp.xoffset = x
			self._periods.append(temp)
			x += temp.width + self._periodspacing

	def __str__(self):
		return(json.dumps(self.structure, indent=2))

	def draw(self, canvas):
		for p in self._periods:
			p.draw(canvas)




##### Main #####

f = open("/Users/rainerstrotmann/Documents/Programming/Python3/trialdesign/test.json")
td = Trialdesign(js=json.load(f), xoffset=100)

surface = cairo.SVGSurface("test1.svg", 700, 700)
canvas = cairo.Context(surface)
canvas.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
canvas.set_font_size(12)

# for p in td.structure["periods"]:
# 	print(p["caption"])
# 	pp = trialperiod(p)
# 	pp.draw(canvas)

td.draw(canvas)


	#canvas.saveSvg('example.svg')
	#canvas.stroke()


	# # creating a rectangle(square) for left eye
	# context.rectangle(100, 100, 100, 100)

	# # creating a rectangle(square) for right eye
	# context.rectangle(500, 100, 100, 100)

	# # creating position for the curves
	# x, y, x1, y1 = 0.1, 0.5, 0.4, 0.9
	# x2, y2, x3, y3 = 0.4, 0.1, 0.9, 0.6

	# # setting scale of the context
	# context.scale(700, 700)

	# # setting line width of the context
	# context.set_line_width(0.04)

	# # move the context to x,y position
	# context.move_to(x, y)

	# # draw the curve for smile
	# context.curve_to(x1, y1, x2, y2, x3, y3)

	# # setting color of the context
	# context.set_source_rgba(0.4, 1, 0.4, 1)

	# # stroke out the color and width property



	# printing message when file is saved
	#print("File Saved")