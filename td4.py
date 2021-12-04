#!/usr/local/bin/python3

import click
import pathlib
import cairo
import json
import random
# import math
import re
import itertools


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

	with open(infile) as f:
		td = Trialdesign(js=json.load(f))
	td.dump(canvas)
	td.render(canvas)

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


def items_names(trial, item):
	out = []
	for p in trial['periods']:
		if 'procedures' in p.keys():
			for proc in p['procedures']:
				out += [proc['caption']]
	return(list(set(out)))	

def procedure_names(trial):
	#return(list(set([c['caption'] for p in trial['periods'] for c in p['procedures']])))
	out = []
	for p in trial['periods']:
		if 'procedures' in p.keys():
			for proc in p['procedures']:
				out += [proc['caption']]
	return(list(set(out)))

def administration_names(trial):
	out = []
	for p in trial['periods']:
		if 'administrations' in p.keys():
			for proc in p['administrations']:
				out += [proc['caption']]
	return(list(set(out)))

	#return(list(set([c['caption'] for p in trial['periods'] for c in p['administrations']])))	




# def extract_procedure(period, caption):
# 	temp = []
# 	for proc in period['procedures']:
# 		if proc['caption'] == caption:
# 			if 'times' in proc.keys():
# 				t = proc['times']
# 			else: 
# 				t = [0]
# 			temp += [(d, t) for d in decode_daylist(proc['days'])]
# 	return(temp)

def extract_procedure(period, caption):
	temp = []
	for x in ['procedures', 'administrations']:
		if x in period.keys():
			for proc in period[x]:
				if proc['caption'] == caption:
					if 'times' in proc.keys():
						t = proc['times']
					else: 
						t = [0]
					temp += [(d, t) for d in decode_daylist(proc['days'])]
	return(temp)

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

# def period_widths(trial, canvas, width_function):
# 	return([period_width(p, canvas, width_function) for p in trial['periods']])

def period_day_starts(period, canvas, xoffset, width_function):
	out=[xoffset]
	acc = xoffset
	for i in width_function(period, canvas):
		acc += i
		out.append(acc)
	return out[:-1]

def period_day_centers(period, canvas, xoffset, width_function):
	return([start + width / 2 for start, width in zip(period_day_starts(period, canvas, xoffset, width_function), width_function(period, canvas))])


#### RENDERING ####

def render_daygrid(period, canvas, xoffset, yoffset, height, width_function):
	canvas.save()
	canvas.set_line_width(1.2)
	canvas.set_source_rgb(0, 0, 0)
	y = yoffset
	for start, width, center, label, shading in zip(period_day_starts(period, canvas, xoffset, width_function), width_function(period, canvas), period_day_centers(period, canvas, xoffset, width_function), day_labels(period), day_shadings(period)):
		if shading:
			canvas.rectangle(start, y, width, height)
			canvas.set_source_rgb(0.85, 0.85, 0.85)
			canvas.fill()
			canvas.set_source_rgb(0, 0, 0)
		canvas.rectangle(start, y, width, height)
		canvas.stroke()
		canvas.move_to(center - textwidth(canvas, str(label)) / 2, yoffset + height - (height- textheight(canvas, "X")) / 2)
		canvas.show_text(str(label))
		canvas.stroke()
	canvas.restore()
	return(height)

def render_dummy(period, canvas, caption, xoffset, yoffset, lineheight, width_function, default_symbol):
	canvas.save()
	canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
	canvas.rectangle(xoffset, yoffset, period_width(period, canvas,width_function), lineheight)
	canvas.fill()
	canvas.restore()
	return

def render_procedure(period, canvas, caption, xoffset, yoffset, lineheight, width_function, default_symbol, debug=False):

	if debug:
		render_dummy(period, canvas, caption, xoffset, yoffset, lineheight, width_function, default_symbol)
	y = yoffset + lineheight/2 # center of the line
	canvas.move_to(5, y + textheight(canvas, caption) * (1/2 - 0.1))
	canvas.show_text(caption)
	positions = period_day_centers(period, canvas, xoffset, width_function)
	widths = width_function(period, canvas)
	symbols = procedure_symbols(period, caption, default_symbol)
	for p, w, s in zip(positions, widths, symbols):
		if s != "":
			render_symbol(canvas, p, y, textheight(canvas, "X"), w, s)
	return(lineheight)

def render_symbol(canvas, x, y, height, width, symbol):
	if symbol == "diamond":
		draw_diamond(canvas, x, y, height)
	elif symbol == "block":
		draw_rect(canvas, x, y, height, width)
	elif symbol == "arrow":
		draw_arrow(canvas, x, y, height, width)
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
	return(out)

def draw_diamond(canvas, x, y, height, size=0.7):
	canvas.save()
	canvas.set_line_width(1.2)
	canvas.set_line_join(cairo.LINE_JOIN_ROUND)
	canvas.set_line_join(cairo.LINE_CAP_ROUND)
	canvas.set_source_rgb(0, 0, 0)
	canvas.move_to(x, y - height*size)
	canvas.line_to(x + height*1/2*size, y)
	canvas.line_to(x, y + height*size)
	canvas.line_to(x - height*1/2*size, y)
	canvas.line_to(x, y - height*size)
	canvas.stroke()
	canvas.restore()

def draw_rect(canvas, x, y, height, width, size=1):
	h = height * .8 * size
	w = width * .7 * size
	canvas.save()
	canvas.set_line_width(1.2)
	canvas.set_source_rgb(0, 0, 0)
	canvas.rectangle(x - w/2, y - h/2,  w, h)
	canvas.stroke()
	canvas.restore()	

def draw_arrow(canvas, x, y, height, width, size=1.2):
	canvas.save()
	canvas.set_line_width(1.4)
	canvas.set_line_join(cairo.LINE_JOIN_ROUND)
	canvas.set_line_join(cairo.LINE_CAP_ROUND)
	canvas.set_source_rgb(0, 0, 0)
	ybase = y - height * size / 2
	yapex = y + height * size / 2
	yarrow = yapex - (yapex - ybase) * .45
	xarrow = (yapex - ybase) * .15
	canvas.move_to(x, ybase)
	canvas.line_to(x, yapex)
	canvas.line_to(x - xarrow, yarrow)
	canvas.move_to(x, yapex)
	canvas.line_to(x + xarrow, yarrow)
	canvas.stroke()
	canvas.restore()

# def draw_dummy(canvas, x_start, x_end, y):
# 	canvas.save()
# 	canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
# 	height = textheight(canvas, "X")
# 	canvas.rectangle(x_start, y-height/2, x_end - x_start, y+height/2)
# 	canvas.fill()
# 	canvas.restore()



class Trialdesign(object):
	def __init__(self, js=dict()):
		self._periods = []
		for p in js["periods"]:
			self._periods.append(p)
		self._td = js

	def render(self, canvas):
		ypadding = 7
		ygap = textheight(canvas, "X")
		periodspacing = textwidth(canvas, "XX"	)
		lineheight = textheight(canvas, "X") * 1.5

		xoffset = max([textwidth(canvas, i) for i in procedure_names(self._td)]) + 30
		yoffset = 10
		x = xoffset
		def render_items(name_function, default_symbol, y):
			for n in name_function(self._td):
				x = xoffset
				for p in self._periods:
					yy = render_procedure(p, canvas, n, x, y, lineheight, period_day_widths, default_symbol, debug=False)
					x += period_width(p, canvas, period_day_widths) + periodspacing
				y += yy + ypadding
			return(y)

		# header
		headerheight = textheight(canvas, "X") * 2
		for p in self._periods:
			yy = render_daygrid(p, canvas, x, yoffset, headerheight, period_day_widths)
			x += period_width(p, canvas, period_day_widths) + periodspacing
		xx = xoffset
		w = [period_width(i, canvas, period_day_widths) for i in self._periods]
		for i in w[:-1]:
			xx += i
			canvas.move_to(xx, yoffset+headerheight/2)
			canvas.line_to(xx + periodspacing, yoffset+headerheight/2)
			xx += periodspacing
		y = yoffset + yy + ygap

		# procedures
		for nf, ds in [(administration_names, "arrow"), (procedure_names, "diamond")]:
			y = render_items(nf, ds, y)


	def dump(self, canvas):
		for p in self._periods:
			# for i in p['administrations']:
			# print(extract_procedure(p, 'itraconazole'))
			# 	print(i)

			# print(f'period width: {period_width(p, canvas, period_day_widths)}')
			# print(f'day widths: {period_day_widths(p, canvas)}')
			# print(f'day starts: {period_day_starts(p, canvas, 100, period_day_widths)}')
			# #print(f'day starts: {period_day_starts(p, canvas, 100, period_day_widths1)}')
			# print(f'day centers: {period_day_centers(p, canvas, 100, period_day_widths)}')
			# print(f'day labels: {day_labels(p)}')
			# print(f'day shading: {day_shadings(p)}')
			# #print(decode_daylist([1, "2", "3-6, 8"]))
			#print(procedure_names(self._td))
			# print(extract_procedure(p, "PK sampling"))
			# print(procedure_symbols(p, "PK sampling", default="arrow"))
			# print(extract_procedure(p, "ECG"))
			print()


if __name__ == "__main__":
	main()