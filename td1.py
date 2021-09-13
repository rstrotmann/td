#!/usr/local/bin/python3

import cairo
import json
import random

class Periodelement(object):
	def __init__(self, period_dict=dict(), length=0, dayheight=20, daywidth=15):
		self._period_dict = period_dict
		self._dayheight = dayheight
		self._daywidth = daywidth
		# self._ypadding = ypadding
		self._length = length
		self._caption = period_dict["caption"]

	def _metrics(self, canvas):
		caption= self._period_dict["caption"].upper()
		(xu, yu, cap_widthu, cap_heightu, dxu, dyu) = canvas.text_extents(caption)
		caption = self._period_dict["caption"]
		#caption = "TEST"
		(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(caption)
		return(caption, cap_width, cap_heightu)	

	def height(self, canvas, ypadding):
		return self._metrics(canvas)[2] + 2 * ypadding

	def width(self):
		return self._length * self._daywidth

	def day_start(self, day):
		return self._daywidth * (day-1)

	def day_center(self, day):
		return self.day_start(day) + self._daywidth*1/2

	def day_am(self, day):
		return self.day_start(day) + self._daywidth*1/6

	def day_pm(self, day):
		return self.day_start(day) + self._daywidth*4/6

	def draw_dummy(self, canvas, x, y, ypadding=7):
		canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
		canvas.rectangle(x, y, self.width(), self.height(canvas, ypadding=ypadding))
		canvas.fill()

	def draw_diamond(self, canvas, x, y, size=0.7):
		canvas.save()
		canvas.set_line_width(1.2)
		canvas.set_source_rgb(0, 0, 0)
		canvas.move_to(x, y-self._dayheight/2*size)
		canvas.line_to(x + self._dayheight*1/4*size, y)
		canvas.line_to(x, y+self._dayheight/2*size)
		canvas.line_to(x - self._dayheight*1/4*size, y)
		canvas.line_to(x, y-self._dayheight/2*size)
		canvas.stroke()
		canvas.restore()

	def draw_arrow(self, canvas, x, y, ypadding=7, size=1.2):
		canvas.save()
		canvas.set_line_width(1.4)
		canvas.set_line_join(cairo.LINE_JOIN_ROUND)
		canvas.set_source_rgb(0, 0, 0)
		ybase = y - self.height(canvas, 0) * size / 2
		yapex = y + self.height(canvas, 0) * size / 2
		yarrow = yapex - (yapex - ybase) * .45
		xarrow = (yapex - ybase) * .15
		canvas.move_to(x, ybase)
		canvas.line_to(x, yapex)
		canvas.line_to(x - xarrow, yarrow)
		canvas.move_to(x, yapex)
		canvas.line_to(x + xarrow, yarrow)
		canvas.stroke()
		canvas.restore()		

	def draw(self, canvas, x, y, ypadding=7, debug=False):
		if debug:
			self.draw_dummy(canvas, x, y, ypadding=ypadding)
		pass

	def dump(self):
		print(json.dumps(self._period_dict, indent=2))



class Procedure(Periodelement):
	def __init__(self, type="generic", **kwargs):
		self._type = type
		Periodelement.__init__(self, **kwargs)
		self._days = self._period_dict["days"]

	@property
	def caption(self):
		return self._caption

	def draw(self, canvas, x, y, ypadding=7, periodspacing=0, debug=False):
		if debug:
			self.draw_dummy(canvas, x, y, ypadding=ypadding)
		yt = y + self.height(canvas, ypadding=ypadding) *1/2
		for i in self._days:
			xt = x + self.day_center(i)
			# self.draw_diamond(canvas, xt, yt)
			self.draw_arrow(canvas, xt, yt, ypadding=ypadding)
		return y + self.height(canvas, ypadding=ypadding)


class Periodcaption(Periodelement):
	def __init__(self, **kwargs):
		Periodelement.__init__(self, **kwargs)

	def draw(self, canvas, x, y, ypadding=7, debug=False):
		Periodelement.draw(self, canvas, x, y, ypadding, debug)
		(caption, cap_width, cap_height) = self._metrics(canvas)
		canvas.set_source_rgb(0, 0, 0)
		canvas.move_to(x + self.width()/2 - cap_width/2, y + cap_height + ypadding)
		canvas.show_text(caption)		



class Periodbox(Periodelement):
	def __init__(self, **kwargs):
		Periodelement.__init__(self, **kwargs)

	def height(self, canvas, ypadding):
		return self._dayheight + 2 * ypadding

	def draw_outline(self, canvas, x, y, ypadding=7, periodspacing=0, dash=False):
		canvas.set_line_width(1.2)
		canvas.set_source_rgb(0, 0, 0)
		canvas.rectangle(x, y + ypadding, self.width(), self._dayheight)
		canvas.stroke()
		canvas.save()
		if dash:
			canvas.set_dash([1.5, 2.5], 1.5)
		# print(periodspacing)
		if periodspacing != 0:
			canvas.move_to(x + self.width(), y + ypadding + self._dayheight/2)
			canvas.line_to(x + self.width() + periodspacing, y + ypadding + self._dayheight/2)
		canvas.stroke()
		canvas.restore()

	def draw_grid(self, canvas, x, y, ypadding=7):
		tx = x
		ty = y
		for i in range(1, self._period_dict["length"]+1):
			canvas.set_line_width(1.2)
			canvas.set_source_rgb(0, 0, 0)
			canvas.rectangle(tx, ty, self._daywidth, self._dayheight)
			canvas.stroke()
			tx += self._daywidth

	def draw_daynumbers(self, canvas, x, y, numbers):
		for n in numbers:
			(nx, ny, n_width, n_height, dx, dy) = canvas.text_extents(str(n))
			canvas.move_to(x + self.day_center(n) - n_width/2, y + self._dayheight/2 + n_height/2)
			canvas.show_text(str(n))
			#self.draw_diamond(canvas, x+self.day_center(n), y=y+self._dayheight*1/2)

	def draw(self, canvas, x, y, ypadding=7, periodspacing=0, draw_grid=True, dash=False, debug=False):
		tx = x
		ty = y + ypadding
		Periodelement.draw(self, canvas, tx, ty, ypadding, debug)
		if draw_grid:
			self.draw_grid(canvas, x, y)
		self.draw_outline(canvas, x, y, ypadding=ypadding, periodspacing=periodspacing, dash=dash)
		canvas.stroke()
		self.draw_daynumbers(canvas, x, y, numbers=[1])
		return 



class Period(object):
	def __init__(self, period_dict=dict(), daywidth=15, dayheight=20, periodspacing=15):
		self._period_dict = period_dict
		self._daywidth = daywidth
		self._dayheight = dayheight
		self._periodspacing = periodspacing
		self._length = period_dict["length"]
		self._elements = []

		self._periodcaption = Periodcaption(period_dict=period_dict, length=self._length, daywidth=daywidth, dayheight=dayheight)

		self._periodbox = Periodbox(period_dict=period_dict, length=self._length, daywidth=daywidth, dayheight=self._dayheight)

		for a in self._period_dict["administrations"]:
			temp = Procedure(type="administration", period_dict=a, daywidth=self._daywidth, length=self._length, dayheight=self._dayheight)
			self._elements.append(temp)

	def dump(self):
		print(json.dumps(self._period_dict, indent=2))

	def draw_structure(self, canvas, x, y, ypadding=7, debug=False):
		yt = y
		self._periodcaption.draw(canvas, x, y, ypadding=ypadding, debug=debug)
		yt += self._periodcaption.height(canvas, ypadding)
		self._periodbox.draw(canvas, x, yt, ypadding=0, periodspacing=self._periodspacing, draw_grid=True, debug=debug)
		yt += self._periodbox.height(canvas, ypadding=0)
		return yt

	def draw_element(self, caption, canvas, x, y, ypadding=7, debug=False):
		e = filter(lambda i: i._caption == caption, self._elements)
		for i in e:
			y = i.draw(canvas, x, y, ypadding=ypadding, debug=debug)
		return y

	def width(self):
		return self._periodbox.width()
	
	

class Cycle(Period):
	def __init__(self, period_dict, **kwargs):
		Period.__init__(self, period_dict=period_dict, daywidth=7, **kwargs)

	def draw_structure(self, canvas, x, y, ypadding=7, debug=False):
		yt = y
		self._periodcaption.draw(canvas, x, yt, ypadding=ypadding, debug=debug)
		yt += self._periodcaption.height(canvas, ypadding)
		self._periodbox.draw(canvas, x, yt, ypadding=0, periodspacing=self._periodspacing, draw_grid=False, dash=True, debug=debug)
		yt += self._periodbox.height(canvas, ypadding=0)
		return yt



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

	def imps(self):
		out = set()
		if "periods" in self._period_dict:
			for p in self._period_dict["periods"]:
				for i in p["administrations"]:
					out.add(i["caption"])
		if "cycles" in self._period_dict:
			for p in self._period_dict["cycles"]:
				for i in p["administrations"]:
					out.add(i["caption"])

		# for i in out:
		# 	for p in self._periods:
		# 		temp = p.draw_element(i)
		return(out)


	def __str__(self):
		return(json.dumps(self.structure, indent=2))

	def draw_structure(self, canvas, xoffset=10, yoffset=10, ypadding=7, debug=False):
		xt = xoffset
		for p in self._periods:
			y = p.draw_structure(canvas, x=xt, y=yoffset, ypadding=ypadding, debug=debug)
			xt += p.width() + p._periodspacing
		return y

	def draw_administrations(self, canvas, x, y, ypadding=7, xcaption=10, debug=False):
		yt = y
		for imp in self.imps():
			# print(imp, x, yt)
			(xu, yu, cap_widthu, cap_heightu, dxu, dyu) = canvas.text_extents(imp.upper())
			canvas.move_to(xcaption, yt + cap_heightu + ypadding)

			# canvas.move_to(10, yt)
			canvas.set_source_rgb(0, 0, 0)
			canvas.show_text(imp)
			canvas.stroke()
			canvas.fill()	
			xt = x
			for p in self._periods:
				temp = p.draw_element(imp, canvas, xt, yt, ypadding=ypadding, debug=debug)
				xt += p.width() + p._periodspacing
			yt = temp
			# y = yt
		return yt



##### Main #####
ypadding= 7
debug = False

surface = cairo.SVGSurface("test1.svg", 700, 700)

canvas = cairo.Context(surface)
canvas.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
canvas.set_font_size(12)

f = open("/Users/rainerstrotmann/Documents/Programming/Python3/trialdesign/test.json")
td = Trialdesign(js=json.load(f))
yt = td.draw_structure(canvas, xoffset=100, ypadding=ypadding, yoffset=10, debug=debug)
# print(td.imps())
td.draw_administrations(canvas, x=100, y=yt, ypadding=ypadding, debug=debug)







f = open("/Users/rainerstrotmann/Documents/Programming/Python3/trialdesign/onco.json")
td1 = Trialdesign(js=json.load(f))
yt = td1.draw_structure(canvas, xoffset=100, yoffset=200, debug=debug)
td1.draw_administrations(canvas, x=100, y=yt, ypadding=ypadding, debug=debug)

# print(td1.imps())
# svg = rsvg.Handle(file="out.svg")
# svg.render_cairo(canvas)

# surface.write_to_png("test.png")
surface.finish()


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