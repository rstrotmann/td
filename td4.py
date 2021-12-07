#!/usr/local/bin/python3

import click
import pathlib
import cairo
import json
import random
import math
import re
import itertools


# to do:#
# implement time scale bracket



@click.command()
@click.argument("file")
@click.option("--fontsize", "-s", type=int, default=11, help='output font size (default 11)')
@click.option("--debug", "-d", is_flag=True, help='debug output')
def main(file, debug, fontsize):
	infile = pathlib.Path(file)
	inpath = pathlib.Path(file).resolve().parent
	outfile = inpath.joinpath(infile.stem + ".svg")

	surface = cairo.SVGSurface(outfile, 1000, 700)
	canvas = cairo.Context(surface)
	canvas.select_font_face("Calibri", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(fontsize)
	canvas.set_line_width(1.2)
	canvas.set_line_join(cairo.LINE_JOIN_ROUND)
	canvas.set_line_join(cairo.LINE_CAP_ROUND)
	canvas.set_source_rgb(0, 0, 0)

	with open(infile) as f:
		td = Trialdesign(js=json.load(f), debug=debug)
	td.render(canvas, width_function=period_day_widths1)


#### Helper functions

def textwidth(canvas, text):
	(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
	return(cap_width)

def textheight(canvas, text):
	(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
	return(cap_height)	

def decode_daylist(daylist):
	days = []
	for i in daylist:
		if isinstance(i, int):
			days.append(i)
		elif isinstance(i, str):
			pat_element = r'(\d+)(-(\d+))?'
			pat = f'({pat_element}(, )*)'
			m = re.findall(pat, i)
			if m:
				for mm in m:
					if mm[3] == "":
						days.append(int(mm[1]))
					else:
						for i in range(int(mm[1]), int(mm[3])+1):
							days.append(i)
	return(days)

def item_names(trial, item_class):
	out = []
	for p in trial['periods']:
		if item_class in p.keys():
			for proc in p[item_class]:
				temp = proc['caption']
				if not temp in out:
					out.append(temp)
	return(out)

def extract_procedure(period, caption):
	temp = []
	for x in ['procedures', 'administrations']:
		if x in period.keys():
			for proc in period[x]:
				if proc['caption'] == caption:
					if 'times' in proc.keys():
						t = proc['times']
					elif 'freq' in proc.keys() and proc['freq'] == 'rich':
						t = [0, 0]
					else: 
						t = [0]
					temp += [(d, t) for d in decode_daylist(proc['days'])]
	return(temp)

def extract_interval(period, caption):
	out = []
	if 'interval' in period.keys():
		for intv in period['intervals']:
			if intv['caption'] == caption:
				out = [intv['start'], intv['duration']]
	return(out)

def extract_times(period, caption):
	temp = extract_procedure(period, caption)
	return([(d-1)*24+t for (d, ts) in temp for t in ts])

def day_index(period, day):
	temp = day - period['start']
	if period['start'] < 0 and day > 0:
		temp -= 1
	return(temp)

def day_labels(period):
	temp = [""] * period['length']
	if "daylabels" in period.keys():
		for i in decode_daylist(period['daylabels']):
			temp[day_index(period, i)] = i
	return(temp)

def day_shadings(period):
	temp = [False] * period['length']
	if "dayshading" in period.keys():
		for i in decode_daylist(period['dayshading'])	:
			temp[day_index(period, i)] = True
	return(temp)

def period_day_widths(period, canvas):
	return([textwidth(canvas, "XX")] * period['length'])

def period_day_widths1(period, canvas):
	return([textwidth(canvas, "XX") if i!="" else 5 for i in day_labels(period)])

def period_width(period, canvas, width_function):
	return(sum(width_function(period, canvas)))

def period_day_starts(period, canvas, xoffset, width_function):
	out=[xoffset]
	acc = xoffset
	for i in width_function(period, canvas):
		acc += i
		out.append(acc)
	return out[:-1]

def period_day_centers(period, canvas, xoffset, width_function):
	return([start + width / 2 for start, width in zip(period_day_starts(period, canvas, xoffset, width_function), width_function(period, canvas))])

def period_day_ends(period, canvas, xoffset, width_function):
	starts = period_day_starts(period, canvas, xoffset, width_function)
	widths = width_function(period, canvas)
	return([s+w for s, w in zip(starts, widths)])


#### Trial design class

class Trialdesign(object):
	def __init__(self, js=dict(), debug=True):
		self._periods = []
		for p in js["periods"]:
			self._periods.append(p)
		self._td = js
		self._debug = debug

	def render(self, canvas, width_function=period_day_widths):
		ypadding = 7
		ylabelpadding = 3
		yheaderpadding = ypadding

		periodspacing = textwidth(canvas, "XX"	)
		headerheight = textheight(canvas, "X") * 2
		lineheight = textheight(canvas, "X") * 1.5

		xoffset = max([textwidth(canvas, i) for i in item_names(self._td, 'procedures')]) + 30
		yoffset = 10

		def safe_render(render_func):
			def wrapper(*args, **kwargs):
				canvas.save()
				out = render_func(*args, **kwargs)
				canvas.stroke()
				canvas.restore()
				return out
			return wrapper

		@safe_render
		def render_dummy(period, xoffset, yoffset, lineheight, debug=False):
			canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
			canvas.rectangle(xoffset, yoffset, period_width(period, canvas, width_function), lineheight)
			canvas.fill()

		@safe_render
		def render_daygrid(period, caption, xoffset, yoffset, height):
			print(width_function(period, canvas))
			y = yoffset
			if self._debug:
				render_dummy(period, xoffset, yoffset, height)
			for start, width, center, label, shading in zip(period_day_starts(period, canvas, xoffset, width_function), width_function(period, canvas), period_day_centers(period, canvas, xoffset, width_function), day_labels(period), day_shadings(period)):
				if shading:
					canvas.rectangle(start, y, width, height)
					canvas.set_source_rgb(0.85, 0.85, 0.85)
					canvas.fill()
					canvas.set_source_rgb(0, 0, 0)
				canvas.rectangle(start, y, width, height)
				canvas.stroke()
				label = str(label)
				delta = textwidth(canvas, "1")*.5 if len(label)>0 and label[0] == "1" else 0
				canvas.move_to(center - textwidth(canvas, str(label)) / 2-delta, yoffset + height - (height- textheight(canvas, "X")) / 2)
				canvas.show_text(str(label))
			return(height)

		@safe_render
		def render_periodcaption(period, caption, xoffset, yoffset, height):
			if self._debug:
				render_dummy(period, xoffset, yoffset, height)
			xcenter = xoffset + period_width(period, canvas, width_function)/2
			canvas.move_to(xcenter - textwidth(canvas, str(period['caption']))/2, yoffset+ height - (height-textheight(canvas, "X"))/2)
			canvas.show_text(str(period['caption']))
			return(height)

		@safe_render
		def render_procedure(period, caption, xoffset, yoffset, lineheight, default_symbol):
			if self._debug:
				render_dummy(period, xoffset, yoffset, lineheight)
			y = yoffset + lineheight/2 # center of the line
			# render procedure name
			canvas.move_to(5, y + textheight(canvas, caption) * (1/2 - 0.1))
			canvas.show_text(caption)
			
			centers = period_day_centers(period, canvas, xoffset, width_function)
			widths = width_function(period, canvas)

			symbols = procedure_symbols(period, caption, default_symbol)
			for p, w, s in zip(centers, widths, symbols):
				if s != "":
					render_symbol(p, y, textheight(canvas, "X"), w, s)
			return(lineheight)

		@safe_render
		def render_interval(period, caption, xoffset, yoffset, lineheight):
			if self._debug:
				render_dummy(period, xoffset, yoffset, lineheight)
			y = yoffset + lineheight/2 # center of the line
			# render procedure name
			canvas.move_to(5, y + textheight(canvas, caption) * (1/2 - 0.1))
			canvas.show_text(caption)
			# render interval box
			starts = period_day_starts(period, canvas, xoffset, width_function)
			ends = period_day_ends(period, canvas, xoffset, width_function)
			height = 0.5 * lineheight
			if 'intervals' in period.keys():
				for intv in period['intervals']:
					if intv['caption'] == caption:
						start, duration = intv['start'], intv['duration']
						startx = starts[day_index(period, start)]
						end = start + duration -1
						if start <0 and end >0:
							end += 1
						endx = ends[day_index(period, end)]
						canvas.rectangle(startx, y-height/2, endx-startx, height)
						canvas.stroke()
			return(lineheight)

		def draw_line(x1, y1, x2, y2):
			canvas.move_to(x1, y1)
			canvas.line_to(x2, y2)

		def draw_text(x, y, caption):
			canvas.move_to(x, y)
			canvas.show_text(str(caption))

		def render_symbol(x, y, height, width, symbol):
			if symbol == "diamond":
				draw_diamond(x, y, height)
			elif symbol == "block":
				draw_rect(x, y, height, width)
			elif symbol == "arrow":
				draw_arrow(x, y, height, width)
			return

		def procedure_symbols(period, caption, default="diamond"):
			temp = extract_procedure(period, caption)
			out = [""] * period['length']
			for (d, t) in temp:
				if len(t) > 1:
					symbol = "block"
				else:
					symbol = default
				out[day_index(period, d)] = symbol
				#print(out)
			return(out)

		@safe_render
		def draw_diamond(x, y, height, size=0.7):
			draw_line(x, y - height*size, x + height*1/2*size, y)
			canvas.line_to(x, y + height*size)
			canvas.line_to(x - height*1/2*size, y)
			canvas.line_to(x, y - height*size)

		@safe_render
		def draw_rect(x, y, height, width, size=1):
			h = height * .8 * size
			w = width * .7 * size
			canvas.rectangle(x - w/2, y - h/2,  w, h)

		@safe_render
		def draw_arrow(x, y, height, width, size=1.2):
			canvas.set_line_width(1.4)
			ybase = y - height * size / 2
			yapex = y + height * size / 2
			yarrow = yapex - (yapex - ybase) * .45
			xarrow = (yapex - ybase) * .15
			draw_line(x, ybase, x, yapex)
			canvas.line_to(x - xarrow, yarrow)
			draw_line(x, yapex, x + xarrow, yarrow)

		@safe_render
		def draw_curly(xstart, xend, y, radius=8):
			xcenter = xstart + (xend - xstart)/2
			canvas.set_line_width(1.4)
			canvas.set_line_join(cairo.LINE_JOIN_ROUND)
			canvas.move_to(xstart, y)
			canvas.arc_negative(xstart+radius, y, radius, math.pi, math.pi/2)
			canvas.line_to(xcenter-2*radius, y+radius)
			canvas.arc(xcenter-radius, y+2*radius, radius, math.pi*1.5, 0)
			canvas.arc(xcenter+radius, y+2*radius, radius, math.pi, math.pi*1.5)
			canvas.move_to(xcenter+radius, y+radius)
			canvas.line_to(xend-radius, y+radius)
			canvas.arc_negative(xend-radius, y, radius, math.pi/2, 0)

		@safe_render
		def render_bracket(period, xoffset, y, startday, endday):
			starts = period_day_starts(period, canvas, xoffset, width_function)
			ends = period_day_ends(period, canvas, xoffset, width_function)
			if day_index(period, startday) < len(starts) and day_index(period, endday) < len(ends):
				startx = starts[day_index(period, startday)]
				endx = ends[day_index(period, endday)]
				draw_curly(startx, endx, y, radius=lineheight/3)
			return(y+lineheight/3)

		def render_periods(x, y, caption, height, render_function, **kwargs):
			for p in self._periods:
				yy = render_function(p, caption, x, y, height, **kwargs)
				x += period_width(p, canvas, width_function) + periodspacing
			return(y + yy)

		def render_times(x, y, period, caption, height):
			times = extract_times(period, caption)
			pw = period_width(period, canvas, width_function) 
			scale_width = pw
			scale_x = x + (pw-scale_width)/2
			scale_y = y + height/2
			scale_factor = scale_width / max(times)
			draw_line(scale_x, scale_y, scale_x+scale_width, scale_y)
			c_width = [textwidth(canvas, str(i)) for i in times]
			c_pos = [scale_x+scale_factor*i for i in times]
			for ti, wi, pi in zip(times, c_width, c_pos):
				draw_line(pi, y, pi, y+height)
				draw_text(pi - wi/2, y+height+ypadding, ti)

			canvas.stroke()
			return


		## rendering proper

		x = xoffset
		y = yoffset

		# header
		y = render_periods(xoffset, y, "", headerheight, render_periodcaption) + ylabelpadding
		y = render_periods(xoffset, y, "", headerheight, render_daygrid) + yheaderpadding

		# render dashes between periods
		xx = x
		w = [period_width(i, canvas, width_function) for i in self._periods]
		for i in w[:-1]:
			xx += i
			draw_line(xx, y-yheaderpadding - headerheight/2, xx+ periodspacing, y-yheaderpadding-headerheight/2)
			xx += periodspacing
			canvas.stroke()

		# intervals, administrations, procedures
		for n in item_names(self._td, 'intervals'):
			y = render_periods(xoffset, y, n, lineheight, render_interval) + ypadding

		for n in item_names(self._td, 'administrations'):
			y = render_periods(xoffset, y, n, lineheight, render_procedure, default_symbol="arrow") + ypadding

		for n in item_names(self._td, 'procedures'):
			y = render_periods(xoffset, y, n, lineheight, render_procedure, default_symbol="diamond") + ypadding

		# xx = xoffset
		# for p in self._periods:
		# 	yy = render_bracket(p, xx, y, 1, 4)
		# 	xx += period_width(p, canvas, width_function) + periodspacing

		print(extract_procedure(self._periods[1], "PK sampling"))
		print(extract_times(self._periods[1], "PK sampling"))

		# p = self._periods[1]
		# d = extract_procedure(p, "PK sampling")
		# dmin = min([x for (x,t) in d])
		# dmax = max([x for (x, t) in d])
		# print(dmin, dmax)
		# xx = xoffset + period_width(self._periods[0], canvas, width_function) + periodspacing
		# y = render_bracket(p, xx, y, dmin, dmax) + ypadding
		# render_times(xx, y, p, "PK sampling", lineheight)

	def dump(self, canvas):
		for p in self._periods:
			pass


if __name__ == "__main__":
	main()