#!/usr/local/bin/python3

import click
import pathlib
import cairo
import json
#import random
#import math
import re
#import itertools


# to do:#
# implement time scale bracket
# clean up functions

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

def svg_line(x1, y1, x2, y2, lwd=1, color="black", dashed=False):
	dash = f'stroke-dasharray: {lwd*3} {lwd*3}' if dashed else ""
	return(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color}; stroke-width:{lwd}; {dash}" />\n')

def svg_rect(x, y, w, h, lwd=1, fill_color="none", line_color="black"):
	return(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" style="stroke:{line_color};  stroke-width:{lwd}; fill:{fill_color};" />\n')

def svg_text(x, y, text):
	return(f'<text x="{x}" y="{y}">{text}</text>\n')

def svg_path(x, y, points, lwd=1, size=1, fill=False, dashed=False):
	fill_color = "black" if fill else "none"
	dash = "stroke-dasharray: 2.5 2.5" if dashed else ""
	(x1, y1) = points[-1]
	out = f'<path d="M{x1*size+x}, {y1*size+y} '
	for (x2, y2) in points:
		out += f'L{x2*size+x}, {y2*size+y} '
	out += f'Z" style="stroke: black; fill: {fill_color}; stroke-width:{lwd}; {dash}" />'
	return(out)	

def svg_symbol(x, y, symbol, size=1, fill=False, lwd=1.2):
	if symbol == "diamond":
		return svg_path(x, y, [(0,-0.5), (0.25, 0), (0, 0.5), (-0.25, 0)], size=size*1.4, lwd=lwd)
	elif symbol == "block":
		return svg_path(x, y, [(-1.5/4, -.25), (1.5/4, -.25), (1.5/4, .25), (-1.5/4, .25)], size=size*1.5, lwd=lwd)
	elif symbol == "arrow":
		return svg_path(x, y, [(-0.03, -0.5), (0.03, -0.5), (0.03, 0), (0.1875, 0), (0.0, 0.5), (-0.1875, 0), (-0.03, 0)], size=size*1.2, lwd=lwd, fill=True)
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

########################################
########################################
########################################


@click.command()
@click.argument("file")
@click.option("--fontsize", "-s", type=int, default=24, help='output font size (default 18)')
@click.option("--condensed", "-c", is_flag=True, help='condensed daygrid')
@click.option("--debug", "-d", is_flag=True, help='debug output')
def main(file, debug, fontsize, condensed):
	debug = debug
	infile = pathlib.Path(file)
	inpath = pathlib.Path(file).resolve().parent
	outfile = inpath.joinpath(infile.stem + ".svg")

	canvas = cairo.Context(cairo.SVGSurface("temp.svg", 10, 10))
	canvas.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(fontsize)

	with open(infile) as f:
		td = json.load(f)
	periods = []
	for p in td["periods"]:
		periods.append(p)


	def textwidth(text):
		(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
		return(cap_width)

	def textheight(text):
		(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
		return(cap_height)

	def period_day_widths(period):
		return([textwidth("XX")] * period['length'])

	def period_day_widths1(period):
		temp=[textwidth("XX") if i!="" else textwidth("XX")/3 for i in day_labels(period)]
		if len(temp)==1:
			temp=[textwidth("XX")]
		return(temp)

	def period_width(period, width_function):
		return(sum(width_function(period)))

	def period_day_starts(period, xoffset, width_function):
		out=[xoffset]
		acc = xoffset
		for i in width_function(period):
			acc += i
			out.append(acc)
		return out[:-1]

	def period_day_centers(period, xoffset, width_function):
		return([start + width / 2 for start, width in zip(period_day_starts(period, xoffset, width_function), width_function(period))])

	def period_day_ends(period, xoffset, width_function):
		starts = period_day_starts(period, xoffset, width_function)
		widths = width_function(period)
		return([s+w for s, w in zip(starts, widths)])
	
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

	def render(width_function=period_day_widths, lwd=1.2, font="Calibri", fontsize=11):
		image_size = 1000
		image_pad = 10
		font = font
		size = fontsize
		line_width = lwd

		# svg_out = f'<svg viewBox="-{image_pad} -{image_pad} {image_size + 2 * image_pad} {image_size + 2 * image_pad}" xmlns="http://www.w3.org/2000/svg">\n'
		# svg_out += f'<style>text {{font-family: {font}; font-size: {size}px ;}}</style>\n'

		svg_out = ""

		ypadding = 7
		ylabelpadding = 3
		yheaderpadding = ypadding*2

		periodspacing = textwidth("XX")
		headerheight = textheight("X")*2
		lineheight = textheight("X")*2

		xoffset = max([textwidth(i) for i in item_names(td, 'procedures') + item_names(td, 'intervals') + item_names(td, 'admininstrations')]) + 30
		yoffset = 10

		def render_dummy(period, xoffset, yoffset, lineheight, debug=False):
			nonlocal svg_out
			svg_out += svg_rect(xoffset, yoffset, period_width(period, width_function), lineheight, lwd=0, fill_color="cornsilk")

		def render_daygrid(period, caption, xoffset, yoffset, height, first_pass=True):
			nonlocal svg_out
			y = yoffset
			if debug:
				render_dummy(period, xoffset, yoffset, height)
			for start, width, center, label, shading in zip(period_day_starts(period, xoffset, width_function), width_function(period), period_day_centers(period, xoffset, width_function), day_labels(period), day_shadings(period)):
				if shading:
					svg_out += svg_rect(start, y, width, height, lwd=0, fill_color="lightgray")
				if width >textwidth("XX")/3:
					svg_out += svg_rect(start, y, width, height, lwd=line_width)
				else:
					svg_out += svg_line(start, y, start+width, y, lwd=line_width, dashed=True)
					svg_out += svg_line(start, y+height, start+width, y+height, lwd=line_width, dashed=True)
				label = str(label)
				delta = textwidth("1")*.5 if len(label)>0 and label[0] == "1" else 0
				svg_out += svg_text(center - textwidth(str(label)) / 2-delta, yoffset + height - (height- textheight("X")) / 2, str(label))
			return(height)

		def render_periodcaption(period, caption, xoffset, yoffset, height, first_pass=True):
			nonlocal svg_out
			if debug:
				render_dummy(period, xoffset, yoffset, height)
			xcenter = xoffset + period_width(period, width_function)/2
			svg_out += svg_text(xcenter - textwidth(str(period['caption']))/2, yoffset+ height - (height-textheight("X"))/2, str(period['caption']))
			return(height)

		def render_procedure(period, caption, xoffset, yoffset, lineheight, default_symbol, first_pass=True):
			nonlocal svg_out
			if debug:
				render_dummy(period, xoffset, yoffset, lineheight)
			y = yoffset + lineheight/2 # center of the line
			if first_pass:
				svg_out += svg_text(5, y + textheight(caption) * (1/2 - 0.1), caption)
			centers = period_day_centers(period, xoffset, width_function)
			widths = width_function(period)
			brackets = extract_decorations(period, caption)
			symbols = procedure_symbols(period, caption, default_symbol)

			for p, w, s, b in zip(centers, widths, symbols, brackets):
				if s != "":
					svg_out += svg_symbol(p, y, s, size=textheight("X"), lwd=line_width)
					if b=="bracketed":
						svg_out += svg_open_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=line_width)
						svg_out += svg_close_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=line_width)
			return(lineheight)

		def render_interval(period, caption, xoffset, yoffset, lineheight, first_pass=True):
			nonlocal svg_out
			if debug:
				render_dummy(period, xoffset, yoffset, lineheight)
			y = yoffset + lineheight/2 # center of the line
			if first_pass:
				svg_out += svg_text(5, y + textheight(caption) * (1/2 - 0.1), caption)
			# render interval box
			starts = period_day_starts(period, xoffset, width_function)
			ends = period_day_ends(period, xoffset, width_function)
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
						svg_out += svg_rect(startx, y-height/2, endx-startx, height, lwd=line_width)
			return(lineheight)

		def render_periods(x, y, caption, height, render_function, **kwargs):
			first = True
			for p in periods:
				yy = render_function(p, caption, x, y, height, first_pass=first, **kwargs)
				x += period_width(p, width_function) + periodspacing
				first=False
			return(y + yy)

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

		#### completed svg output
		out = f'<svg viewBox="-{image_pad} -{image_pad} {image_size + 2 * image_pad} {image_size + 2 * image_pad}" xmlns="http://www.w3.org/2000/svg">\n'
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