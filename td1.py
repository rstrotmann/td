#!/usr/local/bin/python3

import cairo
import json
import random

class Periodelement(object):
	def __init__(self, period_dict=dict(), length=0, dayheight=20, daywidth=15, ypadding=7):
		self._period_dict = period_dict
		self._dayheight = dayheight
		self._daywidth = daywidth
		self._ypadding = ypadding
		self._length = length

	def _metrics(self, canvas):
		caption = self._period_dict["caption"]
		(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(caption)
		return(caption, cap_width, cap_height)	

	def height(self, canvas):
		return self._metrics(canvas)[2] + 2 * self._ypadding

	def width(self):
		return self._length * self._daywidth

	def draw_dummy(self, canvas, x, y):
		canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
		canvas.rectangle(x, y, self.width(), self.height(canvas))
		canvas.fill()

	def draw(self, canvas, x, y, debug=False):
		if debug:
			self.draw_dummy(canvas, x, y)
		pass



# class Procedure(Periodelement):
# 	def __init__(self, type="adminisitration", **kwargs):
# 		self._type = type
# 		Periodelement.__init__(self, **kwargs)

# 	def _metrics(self, canvas):
# 		caption = self._period_dict["caption"]
# 		(cap_x, cap_y, cap_width, cap_height, dx, dy) = canvas.text_extents(caption)
# 		return(caption, cap_width, cap_height)		

# 	def height(self, canvas):
# 		return self._metrics(canvas)[2] + 2 * self._ypadding

# 	def draw_dummy(self, canvas, yoffset):
# 		Periodelement.draw_dummy(self, canvas, yoffset=yoffset, height=self.height(canvas))

# 	def draw(self, canvas, yoffset, periodspacing=0):
# 		if self._debug:
# 			self.draw_dummy(canvas, yoffset=yoffset)
# 		(caption, cap_width, cap_height) = self._metrics(canvas)
# 		canvas.set_source_rgb(0, 0, 0)
# 		canvas.move_to(self._xoffset + self.width/2 - cap_width/2, yoffset + cap_height + self._ypadding)
# 		canvas.show_text(caption)		



class Periodcaption(Periodelement):
	def __init__(self, ypadding=5, **kwargs):
		Periodelement.__init__(self, ypadding=ypadding, **kwargs)

	def draw(self, canvas, x, y, debug=False):
		Periodelement.draw(self, canvas, x, y, debug)
		(caption, cap_width, cap_height) = self._metrics(canvas)
		canvas.set_source_rgb(0, 0, 0)
		canvas.move_to(x + self.width()/2 - cap_width/2, y + cap_height + self._ypadding)
		canvas.show_text(caption)		



class Periodbox(Periodelement):
	def __init__(self, ypadding=0, **kwargs):
		Periodelement.__init__(self, ypadding=ypadding, **kwargs)

	def height(self, canvas):
		return self._dayheight + 2 * self._ypadding

	def draw_outline(self, canvas, x, y, periodspacing=0, dash=False):
		canvas.set_line_width(1)
		canvas.set_source_rgb(0, 0, 0)
		canvas.rectangle(x, y + self._ypadding, self.width(), self._dayheight)
		canvas.stroke()
		canvas.save()
		if dash:
			canvas.set_dash([1, 2], 1)
		if periodspacing != 0:
			canvas.move_to(x + self.width(), y + self._ypadding + self._dayheight/2)
			canvas.line_to(x + self.width() + periodspacing, y + self._ypadding + self._dayheight/2)
		canvas.stroke()
		canvas.restore()

	def draw_grid(self, canvas, x, y):
		tx = x
		ty = y
		for i in range(1, self._period_dict["length"]+1):
			canvas.set_line_width(1)
			canvas.set_source_rgb(0, 0, 0)
			canvas.rectangle(tx, ty, self._daywidth, self._dayheight)
			canvas.stroke()
			tx += self._daywidth

	def draw_daynumbers(canvas, x, y, numbers="1"):
		pass

	def draw(self, canvas, x, y, periodspacing=0, draw_grid=True, dash=False, debug=False):
		tx = x
		ty = y + self._ypadding
		Periodelement.draw(self, canvas, tx, ty, debug)
		if draw_grid:
			self.draw_grid(canvas, x, y)
		self.draw_outline(canvas, x, y, periodspacing=periodspacing, dash=dash)
		canvas.stroke()
		return 



class Period(object):
	def __init__(self, period_dict=dict(), daywidth=15, dayheight=20, periodspacing=15):
		# print(period_dict)
		self._period_dict = period_dict
		self._daywidth = daywidth
		self._dayheight = dayheight
		self._periodspacing = periodspacing
		self._length = period_dict["length"]

		self._periodcaption = Periodcaption(period_dict=period_dict, length=self._length, daywidth=daywidth, dayheight=dayheight, ypadding=7)

		self._periodbox = Periodbox(period_dict=period_dict, length=self._length, daywidth=daywidth, dayheight=dayheight)

		# self._elements = []
		# # add further elements
		# for a in self._period_dict["administrations"]:
		# 	#print(a["caption"])
		# 	self._elements.append(Procedure(type="administration", period_dict=a, length=self._length, daywidth=daywidth, dayheight=dayheight, xoffset=xoffset, yoffset=yoffset, debug=self._debug))
		# for p in self._period_dict["procedures"]:
		# 	#print(p["caption"])
		# 	self._elements.append(Procedure(type=p["caption"], period_dict=p, length=self._length, daywidth=self._daywidth, dayheight=self._dayheight, xoffset=self._xoffset, yoffset=self._yoffset, debug=self._debug))

	def dump(self):
		print(json.dumps(self._period_dict, indent=2))

	def draw(self, canvas, x, y, debug=False):
		yt = y
		self._periodcaption.draw(canvas, x, y, debug=debug)
		yt += self._periodcaption.height(canvas)
		self._periodbox.draw(canvas, x, yt, periodspacing=self._periodspacing, debug=debug)
		yt += self._periodbox.height(canvas)

		# for e in self._elements:
		# 	e.draw(canvas, yoffset=y, periodspacing=self._periodspacing)
		# 	y += e.height(canvas)

	def width(self):
		return self._periodbox.width()
	
	

class Cycle(Period):
	def __init__(self, period_dict, **kwargs):
		Period.__init__(self, period_dict=period_dict, daywidth=7, **kwargs)

	def draw(self, canvas, x, y, debug=False):
		yt = y
		self._periodcaption.draw(canvas, x, yt, debug=debug)
		yt += self._periodcaption.height(canvas)

		self._periodbox.draw(canvas, x, yt, draw_grid=False, periodspacing=10, dash=True, debug=debug)
		yt += self._periodbox.height(canvas)



#############################
#	trial design class
#############################

class Trialdesign(object):
	def __init__(self, js=dict(), periodspacing=15):
		self._period_dict = js
		self._periodspacing = periodspacing
		self._periods = []

		if "periods" in self._period_dict: # period trial
			pp = self._period_dict["periods"]
			for p in pp:
				self._periods.append(Period(p, periodspacing=self._periodspacing * (not p is pp[-1])))

		elif "cycles" in self._period_dict: # cylcle trial
			pp = self._period_dict["cycles"]
			# print(pp)
			for p in pp:
				self._periods.append(Cycle(period_dict=p, periodspacing=self._periodspacing * (p is pp[-1])))


	def __str__(self):
		return(json.dumps(self.structure, indent=2))

	def draw(self, canvas, xoffset=10, yoffset=10):
		xt = xoffset
		for p in self._periods:
			p.draw(canvas, x=xt, y=yoffset, debug=True)
			xt += p.width() + p._periodspacing




##### Main #####

surface = cairo.SVGSurface("test1.svg", 700, 700)
canvas = cairo.Context(surface)
canvas.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
canvas.set_font_size(12)

f = open("/Users/rainerstrotmann/Documents/Programming/Python3/trialdesign/test.json")
td = Trialdesign(js=json.load(f))
td.draw(canvas, xoffset=100, yoffset=10)

f = open("/Users/rainerstrotmann/Documents/Programming/Python3/trialdesign/onco.json")
td1 = Trialdesign(js=json.load(f))
td1.draw(canvas, xoffset=100, yoffset=200)

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