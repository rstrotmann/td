#!/usr/local/bin/python3

import click
import pathlib
import cairo
import json
#import random
import math
import re
#import itertools
import sys


# to do:#
# implement time scale bracket
# clean up functions
# implement broken time axis for PK sampling times after rich period + 24 h
# implement curly bracket start/stop at day center when QD

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
					if 'relative' in proc.keys():
						rel = proc['relative']
					else:
						rel = 1
					temp += [(d, t, rel) for d in decode_daylist(proc['days'])]
	return(temp)

def extract_decorations(period, caption):
	temp = [""] * period['length']
	for x in ['procedures', 'administrations']:
		if x in period.keys():
			for proc in period[x]:
				if proc['caption'] == caption:
					if 'decoration' in proc.keys():
						deco = proc['decoration']
					else:
						deco = ""
					dd = [(d, deco) for d in decode_daylist(proc['days'])]
					for (i, deco) in dd:
						temp[day_index(period, i)] = deco
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
	# print(temp)
	return([(d-rel)*24+t for (d, ts, rel) in temp for t in ts])

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

def svg_line(x1, y1, x2, y2, lwd=1, color="black", dashed=False):
	dash = f'stroke-dasharray: {lwd*3} {lwd*3}' if dashed else ""
	return(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color}; stroke-width:{lwd}; {dash}" />\n')

def svg_rect(x, y, w, h, lwd=1, fill_color="none", line_color="black"):
	return(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" style="stroke:{line_color};  stroke-width:{lwd}; fill:{fill_color};" />\n')

def svg_text(x, y, text):
	return(f'<text x="{x}" y="{y}">{text}</text>\n')

def svg_path(x, y, points, lwd=1, size=1, fill=False, dashed=False, fill_color="none"):
	#fill_color = "black" if fill else "none"
	dash = "stroke-dasharray: 2.5 2.5" if dashed else ""
	(x1, y1) = points[-1]
	out = f'<path d="M{x1*size+x}, {y1*size+y} '
	for (x2, y2) in points:
		out += f'L{x2*size+x}, {y2*size+y} '
	out += f'Z" style="stroke: black; fill: {fill_color}; stroke-width:{lwd}; {dash}" />'
	return(out)	

def svg_symbol(x, y, width, symbol, size=1, fill=False, fill_color="none", lwd=1.2):
	if symbol == "diamond":
		return svg_path(x, y, [(0,-0.5), (0.25, 0), (0, 0.5), (-0.25, 0)], size=size*1.4, lwd=lwd, fill=fill)
	elif symbol == "block":
		w = width/size/1.5*.6
		return svg_path(x, y, [(w/-2, -.25), (w/2, -.25), (w/2, .25), (-w/2, .25)], size=size*1.5, lwd=lwd, fill=fill)
	elif symbol == "arrow":
		return svg_path(x, y, [(-0.03, -0.5), (0.03, -0.5), (0.03, 0), (0.1875, 0), (0.0, 0.5), (-0.1875, 0), (-0.03, 0)], size=size*1.2, lwd=lwd, fill=True, fill_color="black")
	return ""

def svg_open_bracket(x, y, height, width, xpadding=0, radius=3, lwd=1.2):
	h, w = height, width
	r = radius
	d = xpadding
	out = f'<path d="M{x-w/2+r-d}, {y-h/2} A{r}, {r} 0 0,0 {x-w/2-d}, {y-h/2+r}'
	out += f'L{x-w/2-d}, {y+h/2-r} ' 
	out += f'A{r}, {r} 0 0,0 {x-w/2+r-d} {y+h/2}'
	out += f'" style="stroke: black; stroke-width:{lwd}; fill:none" />'
	return(out)

def svg_close_bracket(x, y, height, width, xpadding=0, radius=3, lwd=1.2):
	h, w = height, width
	r = radius
	d = xpadding
	out = f'<path d="M{x+w/2-r+d}, {y-h/2} A{r}, {r} 0 0,1 {x+w/2+d}, {y-h/2+r}'
	out += f'L{x+w/2+d}, {y+h/2-r} ' 
	out += f'A{r}, {r} 0 0,1 {x+w/2-r+d} {y+h/2}'
	out += f'" style="stroke: black; stroke-width:{lwd}; fill:none" />'
	return(out)

def svg_curly(xstart, xend, y, radius=8, lwd=1.2):
	xcenter = xstart + (xend - xstart)/2
	out = f'<path d="M{xstart}, {y} '
	out += f'A{radius}, {radius}, 0, 0 0 {xstart+radius}, {y+radius} '
	out += f'L{xcenter-radius}, {y+radius} '
	out += f'A{radius}, {radius} 0, 0 1 {xcenter}, {y+2*radius} '
	out += f'A{radius}, {radius}, 0, 0 1 {xcenter+radius}, {y+radius} '
	out += f'L{xend-radius}, {y+radius} '
	out += f'A{radius}, {radius} 0, 0 0 {xend}, {y} '
	out += f'" style="stroke: black; stroke-width:{lwd}; fill:none" />'
	return(out)

###### functions not relying on anything:

def procedure_symbols(period, caption, default="diamond"):
	out = [""] * period['length']
	for (d, t, rel) in extract_procedure(period, caption):
		if len(t) > 1:
			symbol = "block"
		else:
			symbol = default
		out[day_index(period, d)] = symbol
	return(out)	


###### functions that rely on day_width_function:

def period_width(period, day_width_function):
	return(sum(day_width_function(period)))

def period_day_starts(period, xoffset, daywidth_function):
	out=[xoffset]
	acc = xoffset
	for i in daywidth_function(period):
		acc += i
		out.append(acc)
	return out[:-1]

def period_day_centers(period, xoffset, daywidth_function):
	return([start + width / 2 for start, width in zip(period_day_starts(period, xoffset, daywidth_function), daywidth_function(period))])

def period_day_ends(period, xoffset, daywidth_function):
	starts = period_day_starts(period, xoffset, daywidth_function)
	widths = daywidth_function(period)
	return([s+w for s, w in zip(starts, widths)])

####### rendering functions

def render_dummy(period, xoffset, yoffset, lineheight, metrics):
	"""renders placeholder box for visual debugging purposes"""
	(daywidth_function, textwidth_function, textheight_function) = metrics
	return(svg_rect(xoffset, yoffset, period_width(period, daywidth_function), lineheight, lwd=0, fill_color="cornsilk"))

def render_daygrid(period, caption, xoffset, yoffset, height, metrics, lwd=1.2, first_pass=True, debug=False):
	"""renders the svg output for the day grid for a period"""
	(daywidth_function, textwidth_function, textheight_function) = metrics
	svg_out = ""
	y = yoffset
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, height, metrics)
	for start, width, center, label, shading in zip(period_day_starts(period, xoffset, daywidth_function), daywidth_function(period), period_day_centers(period, xoffset, daywidth_function), day_labels(period), day_shadings(period)):
		if shading:
			svg_out += svg_rect(start, y, width, height, lwd=0, fill_color="lightgray")
		if width >textwidth_function("XX")/3:
			svg_out += svg_rect(start, y, width, height, lwd=lwd)
		else:
			svg_out += svg_line(start, y, start+width, y, lwd=lwd, dashed=True)
			svg_out += svg_line(start, y+height, start+width, y+height, lwd=lwd, dashed=True)
		label = str(label)
		delta = textwidth_function("1")*.5 if len(label)>0 and label[0] == "1" else 0
		svg_out += svg_text(center - textwidth_function(str(label)) / 2-delta, yoffset + height - (height- textheight_function("X")) / 2, str(label))
	return(svg_out)

def render_periodcaption(period, caption, xoffset, yoffset, height, metrics, lwd=1.2, first_pass=True, debug=False):
	"""renders svg code for the header above the daygrid"""
	(daywidth_function, textwidth_function, textheight_function) = metrics
	svg_out = ""
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, height, metrics)
	xcenter = xoffset + period_width(period, daywidth_function)/2
	return(svg_out + svg_text(xcenter - textwidth_function(str(period['caption']))/2, yoffset+ height - (height-textheight_function("X"))/2, str(period['caption'])))

def render_procedure(period, caption, xoffset, yoffset, lineheight, metrics, default_symbol="diamond", lwd=1.2, first_pass=True, debug=False):
	(daywidth_function, textwidth_function, textheight_function) = metrics
	svg_out = ""
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, lineheight, metrics)
	y = yoffset + lineheight/2 # center of the line
	if first_pass:
		svg_out += svg_text(5, y + textheight_function(caption) * (1/2 - 0.1), caption)
	centers = period_day_centers(period, xoffset, daywidth_function)
	widths = daywidth_function(period)
	brackets = extract_decorations(period, caption)
	symbols = procedure_symbols(period, caption, default_symbol)

	for p, w, s, b in zip(centers, widths, symbols, brackets):
		if s != "":
			svg_out += svg_symbol(p, y, w, s, size=textheight_function("X"), lwd=lwd)
			if b=="bracketed":
				svg_out += svg_open_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=lwd)
				svg_out += svg_close_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=lwd)
	return(svg_out)

def render_interval(period, caption, xoffset, yoffset, lineheight, metrics, lwd=1.2, first_pass=True, debug=False):
	(daywidth_function, textwidth_function, textheight_function) = metrics
	svg_out = ""
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, lineheight, metrics)
	y = yoffset + lineheight/2 # center of the line
	if first_pass:
		svg_out += svg_text(5, y + textheight_function(caption) * (1/2 - 0.1), caption)
	# render interval box
	starts = period_day_starts(period, xoffset, daywidth_function)
	ends = period_day_ends(period, xoffset, daywidth_function)
	widths = daywidth_function(period)

	height = 0.4 * lineheight
	if 'intervals' in period.keys():
		for intv in period['intervals']:
			if intv['caption'] == caption:
				start, duration = intv['start'], intv['duration']
				startx = starts[day_index(period, start)]
				end = start + duration -1
				if start <0 and end >0:
					end += 1
				endx = ends[day_index(period, end)]
				if "decoration" in intv.keys():
					if intv["decoration"] == "bracketed":
						wo = widths[day_index(period, start)]
						wc = widths[day_index(period, end)]
						svg_out += svg_open_bracket(startx, y, lineheight, wo*.6, xpadding=0, radius=lineheight/8, lwd=lwd)
						svg_out += svg_close_bracket(endx, y, lineheight, wc*.6, xpadding=0, radius=lineheight/8, lwd=lwd)
				svg_out += svg_rect(startx, y-height/2, endx-startx, height, lwd=lwd)
	return(svg_out)

# def render_periods(periods, x, y, caption, height, render_function, daywidth_function, textwidth_function, textheight_function, periodspacing, **kwargs):
def render_periods(periods, x, y, caption, height, render_function, metrics, periodspacing, **kwargs):
	(daywidth_function, textwidth_function, textheight_function) = metrics
	first = True
	out = ""
	for p in periods:
		out += render_function(p, caption, x, y, height, metrics, first_pass=first, **kwargs)
		x += period_width(p, daywidth_function) + periodspacing
		first=False
	return(out)


########################################
########################################
########################################


@click.command()
@click.argument("file")
@click.option("--fontsize", "-s", type=int, default=14, help='output font size (default 11)')
@click.option("--condensed", "-c", is_flag=True, help='condensed daygrid')
@click.option("--timescale", "-t", is_flag=True, help='show time scale')
@click.option("--debug", "-d", is_flag=True, help='debug output')
@click.option("--help", "-h", is_flag=True, help='help')
def main(file, debug, fontsize, condensed, timescale, help):
	debug = debug
	infile = pathlib.Path(file)
	inpath = pathlib.Path(file).resolve().parent
	outfile = inpath.joinpath(infile.stem + ".svg")

	canvas = cairo.Context(cairo.SVGSurface("temp.svg", 10, 10))
	canvas.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(fontsize)

	if len(file) == 0:
		sys.exit()

	with open(infile) as f:
		td = json.load(f)
	periods = []
	if "periods" in td.keys():
		for p in td["periods"]:
			periods.append(p)

	def make_textwidth(canvas):
		def textwidth_function(text):
			(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
			return(cap_width)
		return textwidth_function

	def make_textheight(canvas):
		def textheight_function(text):
			(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
			return(cap_height)
		return textheight_function

	textheight_function = make_textheight(canvas)
	textwidth_function = make_textwidth(canvas)

	def make_daywidth_function(textwidth_function, condensed):
		if condensed:
			def daywidth_function(period):
				temp=[textwidth_function("XX") if i!="" else textwidth_function("XX")/3 for i in day_labels(period)]
				if len(temp)==1:
					temp=[textwidth_function("XX")]
				return(temp)
		else:
			def daywidth_function(period):
				return([textwidth_function("XX")] * period['length'])
		return(daywidth_function)

	daywidth_function = make_daywidth_function(textwidth_function, condensed)
	metrics = (daywidth_function, textwidth_function, textheight_function)

	# print(textheight_function("TEST"))
	# print(daywidth_function(periods[1]))
	# print(period_width(periods[1], daywidth_function))
	# print(period_day_starts(periods[1], 0, daywidth_function))
	# print(period_day_ends(periods[1], 0, daywidth_function))
	# print(procedure_symbols(periods[1], "PK sampling"))
	# print(render_dummy(periods[1], 0, 0, 20, daywidth_function))
	# print(render_daygrid(periods[0], 0, 0, 20, daywidth_function, textwidth_function, textheight_function))

	font = "Arial"
	viewport_width = 1000
	viewport_height = 300
	out = f'<svg width="{viewport_width}" height="{viewport_height}" xmlns="http://www.w3.org/2000/svg">\n'
	out += f'<style>text {{font-family: {font}; font-size: {fontsize}px ;}}</style>\n'
	y = 0
	# out += render_periodcaption(periods[1], "", 150, y, 20, metrics, debug=debug)
	# y += 20
	# out += render_daygrid(periods[1], "", 150, y, 20, metrics, debug=debug)
	# y += 20
	# # out += render_procedure(periods[1], "PK sampling tepotinib", 150, y, 20, metrics, "diamond", debug=debug)
	# y += 20
	# out += render_interval(periods[1], "hospitalization", 150, y, 20, metrics, debug=debug)

	out += render_periods(periods, 150, y, "", 20, render_periodcaption, metrics, 10, debug=debug)
	y += 20
	out += render_periods(periods, 150, y, "", 20, render_daygrid, metrics, 10, debug=debug)
	# out += render_periods(periods, 150, y, "", 20, render_daygrid, metrics, 10, debug=debug)

	out += f'</svg>'
	with open("test.svg", "w") as f:
		f.write(out)
	return







	


	def render(width_function=period_day_widths, lwd=1.2, font="Calibri", fontsize=11):
		image_size = 1000
		image_pad = 10
		font = font
		size = fontsize
		line_width = lwd

		svg_out = ""

		ypadding = 7
		ylabelpadding = 3
		yheaderpadding = ypadding*2

		periodspacing = textwidth("XX")
		headerheight = textheight("X")*2
		lineheight = textheight("X")*2

		xoffset = max([textwidth(i) for i in item_names(td, 'procedures') + item_names(td, 'intervals') + item_names(td, 'admininstrations')]) + 30
		yoffset = 10

		# def render_dummy(period, xoffset, yoffset, lineheight, debug=False):
		# 	nonlocal svg_out
		# 	svg_out += svg_rect(xoffset, yoffset, period_width(period, width_function), lineheight, lwd=0, fill_color="cornsilk")

		# def render_daygrid(period, caption, xoffset, yoffset, height, first_pass=True):
		# 	nonlocal svg_out
		# 	y = yoffset
		# 	if debug:
		# 		render_dummy(period, xoffset, yoffset, height)
		# 	for start, width, center, label, shading in zip(period_day_starts(period, xoffset, width_function), width_function(period), period_day_centers(period, xoffset, width_function), day_labels(period), day_shadings(period)):
		# 		if shading:
		# 			svg_out += svg_rect(start, y, width, height, lwd=0, fill_color="lightgray")
		# 		if width >textwidth("XX")/3:
		# 			svg_out += svg_rect(start, y, width, height, lwd=line_width)
		# 		else:
		# 			svg_out += svg_line(start, y, start+width, y, lwd=line_width, dashed=True)
		# 			svg_out += svg_line(start, y+height, start+width, y+height, lwd=line_width, dashed=True)
		# 		label = str(label)
		# 		delta = textwidth("1")*.5 if len(label)>0 and label[0] == "1" else 0
		# 		svg_out += svg_text(center - textwidth(str(label)) / 2-delta, yoffset + height - (height- textheight("X")) / 2, str(label))
		# 	return(height)

		# def render_periodcaption(period, caption, xoffset, yoffset, height, first_pass=True):
		# 	nonlocal svg_out
		# 	if debug:
		# 		render_dummy(period, xoffset, yoffset, height)
		# 	xcenter = xoffset + period_width(period, width_function)/2
		# 	svg_out += svg_text(xcenter - textwidth(str(period['caption']))/2, yoffset+ height - (height-textheight("X"))/2, str(period['caption']))
		# 	return(height)

		# def render_procedure(period, caption, xoffset, yoffset, lineheight, default_symbol, first_pass=True):
		# 	nonlocal svg_out
		# 	if debug:
		# 		render_dummy(period, xoffset, yoffset, lineheight)
		# 	y = yoffset + lineheight/2 # center of the line
		# 	if first_pass:
		# 		svg_out += svg_text(5, y + textheight(caption) * (1/2 - 0.1), caption)
		# 	centers = period_day_centers(period, xoffset, width_function)
		# 	widths = width_function(period)
		# 	brackets = extract_decorations(period, caption)
		# 	symbols = procedure_symbols(period, caption, default_symbol)

		# 	for p, w, s, b in zip(centers, widths, symbols, brackets):
		# 		if s != "":
		# 			svg_out += svg_symbol(p, y, w, s, size=textheight("X"), lwd=line_width)
		# 			if b=="bracketed":
		# 				svg_out += svg_open_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=line_width)
		# 				svg_out += svg_close_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=line_width)
		# 	return(lineheight)

		# def render_interval(period, caption, xoffset, yoffset, lineheight, first_pass=True):
		# 	nonlocal svg_out
		# 	if debug:
		# 		render_dummy(period, xoffset, yoffset, lineheight)
		# 	y = yoffset + lineheight/2 # center of the line
		# 	if first_pass:
		# 		svg_out += svg_text(5, y + textheight(caption) * (1/2 - 0.1), caption)
		# 	# render interval box
		# 	starts = period_day_starts(period, xoffset, width_function)
		# 	ends = period_day_ends(period, xoffset, width_function)
		# 	widths = width_function(period)

		# 	height = 0.4 * lineheight
		# 	if 'intervals' in period.keys():
		# 		for intv in period['intervals']:
		# 			if intv['caption'] == caption:
		# 				start, duration = intv['start'], intv['duration']
		# 				startx = starts[day_index(period, start)]
		# 				end = start + duration -1
		# 				if start <0 and end >0:
		# 					end += 1
		# 				endx = ends[day_index(period, end)]
		# 				if "decoration" in intv.keys():
		# 					if intv["decoration"] == "bracketed":
		# 						wo = widths[day_index(period, start)]
		# 						wc = widths[day_index(period, end)]
		# 						svg_out += svg_open_bracket(startx, y, lineheight, wo*.6, xpadding=0, radius=lineheight/8, lwd=line_width)
		# 						svg_out += svg_close_bracket(endx, y, lineheight, wc*.6, xpadding=0, radius=lineheight/8, lwd=line_width)
		# 				svg_out += svg_rect(startx, y-height/2, endx-startx, height, lwd=line_width)
		# 	return(lineheight)

		def render_times(period, caption, xoffset, yoffset, lineheight, first_pass=True):
			nonlocal svg_out
			if debug:
				render_dummy(period, xoffset, yoffset, lineheight*2)
			proc = extract_procedure(period, caption)
			if len(proc) > 0:
				# print(proc)
				times = list(dict.fromkeys(extract_times(period, caption)))
				# print(times)
				maxtime = max(times)
				break_time = sorted(list([i for i in times if i<24]))[-1] * 1.5
				# print(break_time)
				times_below = len([i for i in times if i<=break_time])
				times_above = len([i for i in times if i>break_time])
				# print(below24, above24)
				# mediantime = times[math.floor(len(times)/2)]
				# print(maxtime, mediantime)
				y = yoffset

				# render curly bracket
				startx = period_day_starts(period, xoffset, width_function)[day_index(period, min([i for (i, t, rel) in proc]))]
				endx = period_day_ends(period, xoffset, width_function)[day_index(period, max([i for (i, t, rel) in proc]))]
				bracketheight = lineheight * 2/3
				svg_out += svg_curly(startx, endx, y, radius=bracketheight/2)
				y += lineheight + ypadding

				# render time scale
				pw = period_width(period, width_function) 
				scale_width = pw * .8
				scale_break = scale_width * times_below/(times_below+times_above) # scale breakpoint

				dx = (pw - scale_width) if startx - yoffset > endx - (yoffset + pw) else 0
				scale_x = xoffset + dx

				def scale_left(time):
					return(scale_x + scale_break/break_time*time)

				def scale_right(time):
					return(scale_x + scale_break +
						(scale_width-scale_break)/(maxtime-24)*(time - 24))

				y += lineheight/2
				svg_out += svg_line(scale_x, y, scale_x + scale_width, y)
			
				c_width = [textwidth(str(i)) for i in times]
				# last_caption_end = 0
				for ti, wi in zip(times, c_width):
					x = scale_left(ti) if ti < 24 else scale_right(ti)
					# print(f'x: {x} - {ti}')
					# svg_out += svg_line(x, y, x, y+lineheight/4)
					svg_out += svg_symbol(x, y-lineheight/2, c_width, "diamond", size=textheight("x"), fill=True)
					# ti_start = x - wi/2	
					# if ti_start > last_caption_end:
					# 	svg_out += svg_text(x - wi/2, y+lineheight + textheight("X"), ti)
					# 	last_caption_end = x + wi/2 + textwidth(".	")

				# render scale and labels
				left_times = list(range(0, int(break_time)+1, 2))
				right_times = list(range(24, int(maxtime)+1, 24))
				print(left_times)
				print(right_times)
				last_label_end = 0
				for ti in left_times:
					x = scale_left(ti)
					wi = textwidth(str(ti))
					ti_start = x-wi/2
					svg_out += svg_line(x, y, x, y+lineheight/4)
					if ti_start > last_label_end:
						svg_out += svg_text(x - wi/2, y+lineheight + textheight("X"), ti)
						last_label_end = x + wi/2 + textwidth("1")
				for ti in right_times:
					x = scale_right(ti)
					wi = textwidth(str(ti))
					ti_start = x-wi/2
					svg_out += svg_line(x, y, x, y+lineheight/4)
					if ti_start > last_label_end:
						svg_out += svg_text(x - wi/2, y+lineheight + textheight("X"), ti)
						last_label_end = x + wi/2 + textwidth("1")

			return(lineheight*3)

		# def render_periods(x, y, caption, height, render_function, **kwargs):
		# 	first = True
		# 	for p in periods:
		# 		yy = render_function(p, caption, x, y, height, first_pass=first, **kwargs)
		# 		x += period_width(p, width_function) + periodspacing
		# 		first=False
		# 	return(y + yy)

		#### complete rendering assembly
		x = xoffset
		y = yoffset

		# header
		y = render_periods(xoffset, y, "", headerheight, render_periodcaption) + ylabelpadding
		y = render_periods(xoffset, y, "", headerheight, render_daygrid) + yheaderpadding

		# render dashes between periods
		xx = x
		w = [period_width(i, width_function) for i in periods]
		for i in w[:-1]:
			xx += i
			svg_out += svg_line(xx, y-yheaderpadding - headerheight/2, xx+ periodspacing, y-yheaderpadding-headerheight/2, lwd=line_width)
			xx += periodspacing

		# intervals, administrations, procedures
		for n in item_names(td, 'intervals'):
			y = render_periods(xoffset, y, n, lineheight, render_interval) + ypadding

		for n in item_names(td, 'administrations'):
			y = render_periods(xoffset, y, n, lineheight, render_procedure, default_symbol="arrow") + ypadding
		for n in item_names(td, 'procedures'):
			y = render_periods(xoffset, y, n, lineheight, render_procedure, default_symbol="diamond") + ypadding

		#### test
		if timescale:
			y = render_periods(xoffset, y, "PK sampling", lineheight, render_times) + ypadding
		#svg_out += svg_curly(100, 180, 100, radius=10)

		#### test end


		viewport_height = y
		temp = xoffset + sum([period_width(i, width_function) for i in periods]) + (len(periods))*periodspacing
		viewport_width = temp


		#### completed svg output
		out = f'<svg width="{viewport_width}" height="{viewport_height}" xmlns="http://www.w3.org/2000/svg">\n'
		out += f'<style>text {{font-family: {font}; font-size: {size}px ;}}</style>\n'
		out += svg_out
		out += f'</svg>'
		return(out)



	wf = period_day_widths1 if condensed else period_day_widths
	out = render(width_function=wf, lwd=fontsize/10, fontsize=fontsize, font="Arial")
	with open(outfile, "w") as f:
		f.write(out)


if __name__ == "__main__":
	main()