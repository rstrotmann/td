#!/usr/local/bin/python3

import click
import pathlib
import cairo
import json
import random
import math

class Periodelement(object):
	def __init__(self, period_dict=dict(), length=0, start=1, dayheight=20, daywidth=15):
		self._period_dict = period_dict
		self._dayheight = dayheight
		self._daywidth = daywidth
		self._length = length
		self._start = start
		self._caption = period_dict["caption"]

	def _metrics(self, canvas):
		caption= self._period_dict["caption"].upper()
		(xu, yu, cap_widthu, cap_heightu, dxu, dyu) = canvas.text_extents(caption)
		caption = self._period_dict["caption"]
		(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(caption)
		return(caption, cap_width, cap_heightu)	

	def _dayposition(self, day):
		temp = day - self._start + 1
		if self._start * day < 0:
			temp -= 1
		return temp

	def height(self, canvas, ypadding):
		return self._metrics(canvas)[2] + 2 * ypadding

	def width(self):
		return self._length * self._daywidth

	def day_start(self, day):
		day = self._dayposition(day)
		return self._daywidth * (day-1)

	def day_end(self, day):
		return self._daywidth * (day)

	def day_center(self, day):
		return self.day_start(day) + self._daywidth*1/2

	def day_am(self, day):
		return self.day_start(day) + self._daywidth*1/6

	def day_pm(self, day):
		return self.day_start(day) + self._daywidth*4/6

	def draw_dummy(self, canvas, x, y, ypadding=7):
		canvas.save()
		canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
		canvas.rectangle(x, y, self.width(), self.height(canvas, ypadding=ypadding))
		canvas.fill()
		canvas.restore()

	def draw_rect(self, canvas, x, y, ypadding=7, size=.8):
		h = self._dayheight*.5*size
		w = self._daywidth*.8*size
		canvas.save()
		canvas.set_line_width(1.2)
		canvas.set_source_rgb(0, 0, 0)
		canvas.rectangle(x-w/2, y-h/2,  w, h)
		canvas.stroke()
		canvas.restore()		

	def draw_diamond(self, canvas, x, y, ypadding=7, size=0.6):
		canvas.save()
		canvas.set_line_width(1.2)
		canvas.set_line_join(cairo.LINE_JOIN_ROUND)
		canvas.set_line_join(cairo.LINE_CAP_ROUND)
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
		canvas.set_line_join(cairo.LINE_CAP_ROUND)
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

	def draw_curly(self, canvas, xstart, xend, y, ypadding=7, radius=8, debug=False):
		xcenter = xstart + (xend - xstart)/2
		canvas.save()
		canvas.set_line_width(1.4)
		canvas.set_line_join(cairo.LINE_JOIN_ROUND)
		canvas.set_source_rgb(0, 0, 0)
		canvas.move_to(xstart, y)
		canvas.arc_negative(xstart+radius, y, radius, math.pi, math.pi/2)
		canvas.line_to(xcenter-2*radius, y+radius)
		canvas.arc(xcenter-radius, y+2*radius, radius, math.pi*1.5, 0)
		canvas.arc(xcenter+radius, y+2*radius, radius, math.pi, math.pi*1.5)
		canvas.move_to(xcenter+radius, y+radius)
		canvas.line_to(xend-radius, y+radius)
		canvas.arc_negative(xend-radius, y, radius, math.pi/2, 0)
		canvas.stroke()
		canvas.restore()	

	def draw_interval(self, canvas, x, y, ndays, ypadding=7, size=0.8):
		h = self._dayheight*.5*size
		canvas.save()
		canvas.set_line_width(1.2)
		canvas.set_source_rgb(0, 0, 0)
		canvas.rectangle(x, y-h/2, ndays*self._daywidth+1, h)
		canvas.stroke()
		canvas.restore()

	def draw(self, canvas, x, y, ypadding=7, debug=False):
		if debug:
			self.draw_dummy(canvas, x, y, ypadding=ypadding)
		pass

	def dump(self):
		print(json.dumps(self._period_dict, indent=2))


class Procedure(Periodelement):
	def __init__(self, type="generic", days=[], **kwargs):
		self._type = type
		Periodelement.__init__(self, **kwargs)
		self._days = self._period_dict["days"]

	@property
	def caption(self):
		return self._caption

	def draw(self, canvas, x, y, ypadding=7, periodspacing=0, type="diamond", debug=False):
		if debug:
			self.draw_dummy(canvas, x, y, ypadding=ypadding)
		yt = y + self.height(canvas, ypadding=ypadding) *1/2
		for i in self._days:
			xt = x + self.day_center(i)
			if type=="arrow":
				self.draw_arrow(canvas, xt, yt, ypadding=ypadding)
			if type=="diamond":
				self.draw_diamond(canvas, xt, yt, ypadding=ypadding)
			if type=="rect":
				self.draw_rect(canvas, xt, yt, ypadding=ypadding)
		return y + self.height(canvas, ypadding=ypadding)


class Interval(Procedure):
	def __init__(self, **kwargs):
		Periodelement.__init__(self, **kwargs)
		pd = self._period_dict
		self._begin = pd["start"]
		self._type = "generic"
		if "duration" in pd:
			d = pd["duration"]
			self._end = self._start + d
			self._duration = d
			## correct for negative day numbers
		if "end" in pd:
			self._end = pd["end"]
			self._duration = pd["end"] - self._start

	def draw(self, canvas, x, y, ypadding=7, periodspacing=0, type="interval", debug=False):
		if debug:
			self.draw_dummy(canvas, x, y, ypadding=ypadding)
		yt = y + self.height(canvas, ypadding=ypadding) * 1/2
		xt = x + self.day_start(self._begin)
		self.draw_interval(canvas, xt, yt, self._duration)
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
		canvas.save()
		canvas.set_font_size(self._dayheight*.5)
		for n in numbers:
			(nx, ny, n_width, n_height, dx, dy) = canvas.text_extents(str(n))
			canvas.move_to(x + self.day_center(n) - n_width/2, y + self._dayheight/2 + n_height/2)
			canvas.show_text(str(n))
		canvas.restore()

	def draw(self, canvas, x, y, ypadding=7, periodspacing=0, draw_grid=True, dash=False, debug=False):
		tx = x
		ty = y + ypadding
		Periodelement.draw(self, canvas, tx, ty, ypadding, debug)
		if draw_grid:
			self.draw_grid(canvas, x, y)
		self.draw_outline(canvas, x, y, ypadding=ypadding, periodspacing=periodspacing, dash=dash)
		canvas.stroke()
		numbers=[self._start, 1]
		if "daylabels" in self._period_dict:
			numbers = self._period_dict["daylabels"]
		self.draw_daynumbers(canvas, x, y, numbers=numbers)
		return 


class Period(object):
	def __init__(self, period_dict=dict(), daywidth=15, dayheight=20, periodspacing=15):
		self._period_dict = period_dict
		self._daywidth = daywidth
		self._dayheight = dayheight
		self._periodspacing = periodspacing
		self._length = period_dict["length"]
		self._start = 1
		if "start" in self._period_dict:
			self._start = period_dict["start"]
		self._elements = []

		pd = self._period_dict
		self._periodcaption = Periodcaption(period_dict=period_dict, length=self._length, start=self._start, daywidth=daywidth, dayheight=dayheight)

		self._periodbox = Periodbox(period_dict=period_dict, length=self._length, start=self._start, daywidth=daywidth, dayheight=self._dayheight)

		# intervals
		if "intervals" in pd:
			for i in self._period_dict["intervals"]:
				self._elements.append(Interval(period_dict=i, daywidth=self._daywidth, dayheight=self._dayheight, start=self._start, length=self._length))

		for (t, l) in [("administrations", "administration"), ("procedures", "procedure")]:
			if t in pd:
				for i in pd[t]:
					self._elements.append(Procedure(type=l, period_dict=i, daywidth=self._daywidth, dayheight=self._dayheight, length=self._length, start=self._start))

	def dump(self):
		print(json.dumps(self._period_dict, indent=2))

	def draw_structure(self, canvas, x, y, ypadding=7, draw_grid=True, debug=False):
		yt = y
		self._periodcaption.draw(canvas, x, y, ypadding=ypadding, debug=debug)
		yt += self._periodcaption.height(canvas, ypadding)
		self._periodbox.draw(canvas, x, yt, ypadding=0, periodspacing=self._periodspacing, draw_grid=draw_grid, debug=debug)
		yt += self._periodbox.height(canvas, ypadding=0)
		return yt

	def has_element(self, caption):
		e = filter(lambda i: i._caption == caption, self._elements)
		return len(list(e)) > 0

	def draw_element(self, caption, canvas, x, y, type="diamond", ypadding=7, debug=False):
		e = filter(lambda i: i._caption == caption, self._elements)
		yy = y
		for i in e:
			if i._type == "administration":
				t = "arrow"
			elif "freq" in i._period_dict and i._period_dict["freq"] == "rich":
				t = "rect"
			else:
				t = "diamond"
			yy = i.draw(canvas, x, y, ypadding=ypadding, type=t, debug=debug)
		return yy

	def width(self):
		return self._periodbox.width()
		

class Cycle(Period):
	def __init__(self, period_dict, **kwargs):
		Period.__init__(self, period_dict=period_dict, **kwargs)

	def draw_structure(self, canvas, x, y, ypadding=7, draw_grid=True, debug=False):
		yt = y
		self._periodcaption.draw(canvas, x, yt, ypadding=ypadding, debug=debug)
		yt += self._periodcaption.height(canvas, ypadding)
		self._periodbox.draw(canvas, x, yt, ypadding=0, periodspacing=self._periodspacing, draw_grid=False, dash=True, debug=debug)
		yt += self._periodbox.height(canvas, ypadding=0)
		return yt


class Trialdesign(object):
	def __init__(self, js=dict(), daywidth=14, dayheight=20, periodspacing=12):
		self._period_dict = js
		self._periodspacing = periodspacing
		self._daywidth = daywidth
		self._dayheight = dayheight
		self._periods = []

		if "periods" in self._period_dict: # period trial
			pp = self._period_dict["periods"]
			for p in pp:
				self._periods.append(Period(p, daywidth=self._daywidth, dayheight=self._dayheight, periodspacing=self._periodspacing * (not p is pp[-1])))

		elif "cycles" in self._period_dict: # cylcle trial
			pp = self._period_dict["cycles"]
			for p in pp:
				self._periods.append(Cycle(period_dict=p, daywidth=self._daywidth, dayheight=self._dayheight, periodspacing=self._periodspacing * (p is pp[-1])))

	def items(self, item):
		out = list()
		if "periods" in self._period_dict:
			for p in self._period_dict["periods"]:
				if item in p:
					for i in p[item]:
						out.append(i["caption"])
		if "cycles" in self._period_dict:
			for p in self._period_dict["cycles"]:
				if item in p:
					for i in p[item]:
						out.append(i["caption"])
		return(list(dict.fromkeys(out)))		

	def __str__(self):
		return(json.dumps(self.structure, indent=2))

	def draw_structure(self, canvas, xoffset=10, yoffset=10, ypadding=7, draw_grid=True, debug=False):
		xt = xoffset
		for p in self._periods:
			y = p.draw_structure(canvas, x=xt, y=yoffset, ypadding=ypadding, draw_grid=draw_grid, debug=debug)
			xt += p.width() + p._periodspacing
			y += self._dayheight*1/4
		return y

	def draw_item(self, item, symbol, canvas, x, y, ypadding=7, xcaption=10, debug=False):
		yt = y
		for i in self.items(item):
			h = canvas.text_extents(i.upper())[3]
			canvas.move_to(xcaption, yt + h + ypadding)
			canvas.show_text(i)
			canvas.stroke()
			canvas.fill()	
			xt = x
			for p in self._periods:
				if p.has_element(i):
					temp = p.draw_element(i, canvas, xt, yt, ypadding=ypadding, type=symbol, debug=debug)
				xt += p.width() + p._periodspacing
			yt = temp
		return yt

	def draw_intervals(self, canvas, x, y, ypadding=7, xcaption=10, debug=False):
		return self.draw_item("intervals", "interval", canvas, x, y, ypadding=ypadding, xcaption=xcaption, debug=debug)

	def draw_administrations(self, canvas, x, y, ypadding=7, xcaption=10, debug=False):
		return self.draw_item("administrations", "arrow", canvas, x, y, ypadding=ypadding, xcaption=xcaption, debug=debug)

	def draw_procedures(self, canvas, x, y, ypadding=7, xcaption=10, debug=False):
		return self.draw_item("procedures", "diamond", canvas, x, y, ypadding=ypadding, xcaption=xcaption, debug=debug)

	def draw(self, canvas, x, y, draw_grid=True, ypadding=7, debug=False):
		temp = self.items("administrations") + self.items("procedures")
		xoffset = max([canvas.text_extents(i)[4] for i in temp]) + self._daywidth*2
		yt = self.draw_structure(canvas, xoffset=xoffset, ypadding=ypadding, yoffset=10, draw_grid=draw_grid, debug=debug)
		yt = self.draw_intervals(canvas, x=xoffset, y=yt, ypadding=ypadding, debug=debug)
		yt = self.draw_administrations(canvas, x=xoffset, y=yt, ypadding=ypadding, debug=debug)
		yt = self.draw_procedures(canvas, x=xoffset, y=yt, ypadding=ypadding, debug=debug)



##### Main #####

@click.command()
@click.argument("file")
@click.option("--ypadding", "-y", type=int, default=6, help='vertical padding (default 6)')
@click.option("--fontsize", "-f", type=int, default=11, help='output font size (default 11)')
@click.option("--daywidth", "-w", type=int, default=14, help='width of days (default 14)')
@click.option("--dayheight", "-h", type=int, default=20, help='height of days (default 20)')
@click.option("--debug", "-d", is_flag=True, help='debug output')
def main(file, debug, ypadding, fontsize, daywidth, dayheight):
	infile = pathlib.Path(file)
	inpath = pathlib.Path(file).resolve().parent
	outfile = inpath.joinpath(infile.stem + ".svg")

	# if infile.is_absolute():
	# 	print("absolute path")

	surface = cairo.SVGSurface(outfile, 1000, 700)
	canvas = cairo.Context(surface)
	canvas.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(fontsize)

	f = open(infile)
	td = Trialdesign(js=json.load(f), daywidth=daywidth, dayheight=dayheight)
	td.draw(canvas, 10, 10, draw_grid=True, ypadding=ypadding, debug=debug)
	surface.finish()


if __name__ == "__main__":
	main()
