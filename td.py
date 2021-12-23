#!/opt/homebrew/bin/python3

import click
import pathlib
import cairo
import json
import math
import re
import sys


def assert_period_format(period):
	try:
		assert "caption" in period.keys()
		assert "start" in period.keys() and type(period["start"])==int
		assert "length" in period.keys() and type(period["length"])==int
	except:
		raise TypeError(f'Minimum required fields: Caption start and length')
	try:
		assert period["length"] >= 1
	except:
		raise TypeError(f'Length must be at least 1 day')


def assert_procedure_format(procedure):
	try:
		assert "caption" in procedure.keys()
		assert "days" in procedure.keys()
	except:
		raise TypeError(f'Minimum required fields: Caption and days')


def assert_interval_format(interval):
	try:
		assert "caption" in interval.keys()
		assert "start" in interval.keys()
	except:
		raise TypeError(f'Minimum required fields: Caption, start and duration')
	try:
		assert "duration" in interval.keys() and interval["duration"]>0
	except:
		raise IndexError(f'duration must be positive number')


def decode_daylist(daylist):
	days = []
	if not isinstance(daylist, list):
		daylist = [daylist]
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
	unit = "cycles" if "cycles" in trial.keys() else "periods"
	for p in trial[unit]:
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


def normalize_procedure(procedure):
	"""break down times to days"""
	out = []
	for (d, t, rel) in procedure:
		dd = 0
		while t:
			out.append((d+dd, [i for i in t if i<24], rel))
			t = [i-24 for i in t if i>=24]
			dd += 1
	return(out)


def unnormalize_procedure(procedure):
	out = []
	if procedure:
		rels = set([r for (d, ts, r) in procedure])
		for rel in rels:
			current_times = []
			for (d, ts, r) in procedure:
				for t in ts:
					if r==rel:
						current_times.append(t+(d-r)*24)
			out.append((rel, current_times, rel))	
	return(out)


def has_timescale(period, caption):
	temp = False
	for x in ['procedures', 'administrations']:
		if x in period.keys():
			for proc in period[x]:
				if proc['caption'] == caption:
					if 'timescale' in proc.keys():
						if proc['timescale'] == 'show':
							temp = True
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
					for (day, dec) in dd:
						temp[day_index(period, day)] = dec
	return(temp)


def extract_doses(period, caption):
	temp = [""] * period['length']
	for x in ['procedures', 'administrations']:
		if x in period.keys():
			for proc in period[x]:
				if proc['caption'] == caption:
					if 'dose' in proc.keys():
						dose = proc['dose']
					else:
						dose = ""
					dd = [(d, dose) for d in decode_daylist(proc['days'])]
					for (day, dec) in dd:
						temp[day_index(period, day)] = dec
	return(temp)


def extract_interval(period, caption):
	out = []
	if 'interval' in period.keys():
		for intv in period['intervals']:
			if intv['caption'] == caption:
				out = [intv['start'], intv['duration']]
	return(out)


def extract_times(period, caption):
	temp = normalize_procedure(extract_procedure(period, caption))
	return([(d-rel)*24+t for (d, ts, rel) in temp for t in ts])


def day_index(period, day):
	temp = day - period['start']
	if period['start'] < 0 and day > 0:
		temp -= 1
	if temp <0 or temp>period["length"]-1:
		raise IndexError(f'day index {day} out of range ({period["start"]} to {period["start"]+period["length"]})')
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
		for i in decode_daylist(period['dayshading']):
			idx = day_index(period, i)
			# if idx<0 or idx>len(temp)-1:
			# 	raise IndexError(f'day shading ({i}) out of range in period {period["caption"]}')
			# else:
			temp[idx] = True
	return(temp)


def svg_line(x1, y1, x2, y2, lwd=1, color="black", dashed=False):
	dash = f'stroke-dasharray: {lwd*3} {lwd*3}' if dashed else ""
	return(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color}; stroke-width:{lwd}; {dash}" />\n')


def svg_rect(x, y, w, h, lwd=1, fill_color="none", line_color="black"):
	return(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" style="stroke:{line_color};  stroke-width:{lwd}; fill:{fill_color};" />\n')


def svg_circle(x, y, r, lwd=1.2, fill_color="none", line_color="black"):
	return(f'<circle cx="{x}" cy="{y}" r="{r}" style="stroke:{line_color};  stroke-width:{lwd}; fill:{fill_color};"/>\n')


def svg_text(x, y, text):
	return(f'<text x="{x}" y="{y}">{text}</text>\n')


def svg_path(x, y, points, lwd=1, size=1, fill=False, dashed=False, fill_color="none", title=""):
	title=""
	dash = "stroke-dasharray: 2.5 2.5" if dashed else ""
	(x1, y1) = points[-1]
	out = f'<path d="M{x1*size+x}, {y1*size+y} '
	for (x2, y2) in points:
		out += f'L{x2*size+x}, {y2*size+y} '
	out += f'Z" style="stroke: black; fill: {fill_color}; stroke-width:{lwd}; {dash}"'
	if title != "":
		out += f'><title>{title}</title></path>'
	else:
		out += ' />'
	return(out)	


def svg_symbol(x, y, width, symbol, size=1, fill=False, fill_color="none", lwd=1.2, title=""):
	if symbol == "diamond":
		return svg_path(x, y, [(0,-0.5), (0.25, 0), (0, 0.5), (-0.25, 0)], size=size*1.4, lwd=lwd, fill=fill, title=title)
	elif symbol == "block":
		w = width/size/1.5*.6
		return svg_path(x, y, [(w/-2, -.25), (w/2, -.25), (w/2, .25), (-w/2, .25)], size=size*1.5, lwd=lwd, fill=fill, title=title)
	elif symbol == "arrow":
		return svg_path(x, y, [(-0.03, -0.5), (0.03, -0.5), (0.03, 0), (0.1875, 0), (0.0, 0.5), (-0.1875, 0), (-0.03, 0)], size=size*1.2, lwd=lwd, fill=True, fill_color="black", title=title)
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


def svg_curly_up(xstart, xend, y, radius=8, lwd=1.2):
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


def procedure_symbols(period, caption, default="diamond"):
	out = [""] * (period['length']+1)
	for (d, t, rel) in normalize_procedure(extract_procedure(period, caption)):
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


####### functions that rely on the metrics

def render_dummy(period, xoffset, yoffset, lineheight, metrics):
	"""renders placeholder box for visual debugging purposes. Output is svg code only."""
	daywidth_function = metrics[0]
	return(svg_rect(xoffset, yoffset, period_width(period, daywidth_function), lineheight, lwd=0, fill_color="cornsilk"))


def render_daygrid(period, caption, xoffset, yoffset, height, metrics, style, first_pass=True):
	"""renders the svg output for the day grid for a period. Output is [svg_output, height]"""
	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	svg_out = ""
	y = yoffset

	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, height, metrics)

	for start, width, center, label, shading in zip(period_day_starts(period, xoffset, daywidth_function), daywidth_function(period), period_day_centers(period, xoffset, daywidth_function), day_labels(period), day_shadings(period)):
		if shading:
			svg_out += svg_rect(start, y, width, height, lwd=0, fill_color="lightgray")
		if width > textwidth_function("XX")/3:
			svg_out += svg_rect(start, y, width, height, lwd=lwd)
		else:
			svg_out += svg_line(start, y, start+width, y, lwd=lwd, dashed=True)
			svg_out += svg_line(start, y+height, start+width, y+height, lwd=lwd, dashed=True)
		label = str(label)
		delta = textwidth_function("1")*.5 if label and label[0] == "1" else 0
		svg_out += svg_text(center - textwidth_function(str(label)) / 2-delta, yoffset + height - (height- textheight_function("X")) / 2, str(label))
	return([svg_out, height+ypadding*2])


def render_periodcaption(period, caption, xoffset, yoffset, height, metrics, style, first_pass=True):
	"""render caption for period. The 'caption' input is ignored and the caption field of the input period is used. Output is [svg_output, height]"""
	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	svg_out = ""
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, height, metrics)
	xcenter = xoffset + period_width(period, daywidth_function)/2
	svg_out += svg_text(xcenter - textwidth_function(str(period['caption']))/2, yoffset+ height - (height-textheight_function("X"))/2, str(period['caption']))
	return([svg_out, height+ypadding/2])


def render_procedure(period, caption, xoffset, yoffset, lineheight, metrics, style, default_symbol="diamond", first_pass=True):
	"""render procedure. Output is [svg_output, height]"""

	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

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
	dlabels = day_labels(period)

	ellipses = [1 if (s!="" and l == "" and len(symbols)>3) else 0 for (s,l) in zip(symbols, dlabels)]

	for p, w, s, b, e in zip(centers, widths, symbols, brackets, ellipses):
		if s:
			if e==1 and b=="" and s=="arrow" and ellipsis:
				svg_out += svg_circle(p, y, lineheight/30, fill_color="black")
			else:
				svg_out += svg_symbol(p, y, w, s, size=textheight_function("X"), lwd=lwd, title=caption)
				if b=="bracketed":
					svg_out += svg_open_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=lwd)
					svg_out += svg_close_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=lwd)
	return([svg_out, lineheight+ypadding])


def render_dose_graph(period, caption, xoffset, yoffset, lineheight, metrics, style, first_pass=True):
	"""render dose over time for administration. Output is [svg_output, height]"""

	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	svg_out = ""
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, lineheight+ textheight_function("X"), metrics)

	startx = period_day_starts(period, xoffset, daywidth_function)
	endx = period_day_ends(period, xoffset, daywidth_function)
	doses = [i for i in extract_doses(period, caption)]

	maxdose, mindose = max(doses), min(doses)

	def dosey(dose):
		return(yoffset + lineheight*0.6 - (dose-mindose)/(maxdose-mindose)*lineheight*0.6)

	if doses:
		lastx, lasty, lastdose = 0, 0, 0
		lastend = 0
		for (s, e, d) in zip(startx, endx, doses):
			if type(d)==int or type(d)==float:
				svg_out += svg_line(s, dosey(d), e, dosey(d), lwd=lwd)
				if lasty:
					svg_out += svg_line(lastx, lasty, s, dosey(d), lwd=lwd)
				lastx, lasty = e, dosey(d)
				if d != lastdose:
					if lastend + textwidth_function("n") < s:
						svg_out += svg_text(s, yoffset + lineheight + textheight_function("X"), str(d))
						lastend = s + textwidth_function(str(d))
					lastdose = d
	return([svg_out, lineheight+textheight_function("X")+ypadding])


def render_interval(period, caption, xoffset, yoffset, lineheight, metrics, style, first_pass=True):
	"""render interval for procedure. Output is [svg_output, height]"""

	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	svg_out = ""
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, lineheight, metrics)

	y = yoffset + lineheight/2
	if first_pass:
		svg_out += svg_text(5, y + textheight_function(caption) * (1/2 - 0.1), caption)
	# render interval box
	starts = period_day_starts(period, xoffset, daywidth_function)
	ends = period_day_ends(period, xoffset, daywidth_function)
	widths = daywidth_function(period)

	height = 0.4 * lineheight
	if 'intervals' in period.keys():
		for intv in period['intervals']:
			try:
				assert_interval_format(intv)
			except Exception as err:
				raise TypeError(f'{period["caption"]}, interval "{intv["caption"]}": {err}')
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
	return([svg_out, lineheight+ypadding])


def render_times(period, caption, xoffset, yoffset, lineheight, metrics, style, maxwidth=100):
	"""render timescale for procedure. Output is [svg_output, height]"""

	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	out = ""
	if debug:
		out += render_dummy(period, xoffset, yoffset, lineheight*2 + ypadding*3 + lineheight/6 + textheight_function("X"), metrics)

	proc = normalize_procedure(extract_procedure(period, caption))
	if proc:
		y = yoffset
		times = unnormalize_procedure(proc)[0][1]
		maxtime = max(times)
		break_time = min(sorted(list([i for i in times if i<24]))[-1] + 2, 23)
		times_below = len([i for i in times if i<=break_time])
		times_above = len([i for i in times if i>break_time])

		firstrel = proc[0][2]
		startx = period_day_starts(period, xoffset, daywidth_function)[day_index(period, min([i for (i, t, rel) in proc if rel==firstrel]))]
		endx = period_day_ends(period, xoffset, daywidth_function)[day_index(period, max([i for (i, t, rel) in proc if rel==firstrel]))]

		bracketheight = lineheight * 2/3
		out += svg_curly_up(startx, endx, y, radius=bracketheight/2, lwd=lwd)
		y += lineheight*2 + ypadding*1.5

		scale_height = lineheight/3
		scale_width = min(len(times) * textwidth_function("XX"), maxwidth-xoffset)
		scale_break = scale_width * times_below/(times_below+times_above)
		scale_gap = textwidth_function("m")

		def render_scale(x, y, width, height, scale_min, scale_max, scale_labels):
			out = svg_line(x, y, x+width, y, lwd=lwd)
			label_widths = [textwidth_function(str(i)) for i in scale_labels]
			last_label_end = 0
			for i, wi in zip(scale_labels, label_widths):
				xi = (i-scale_min) * width/(scale_max-scale_min) + x
				out += svg_line(xi, y-height/2, xi, y+height/2, lwd=lwd)
				dxi = wi/2
				if xi-dxi > last_label_end:
					# if i == scale_labels[-1]:
					# 	i = str(i) + " h"
					out += svg_text(xi-dxi, y+height/2+textheight_function("X")+ypadding, str(i))
					last_label_end = xi+dxi+textwidth_function(".")
			return(out)

		def render_points(x, y, width, scale_min, scale_max):
			points = [t for t in times if t>=scale_min and t<=scale_max]
			points_x = [(i-scale_min) * width/(scale_max-scale_min) + x for i in points]
			out = ""
			for p, xi in zip(points, points_x):
				out += svg_symbol(xi, y - lineheight/2-ypadding/2, 0, "diamond", size=textheight_function("X"), lwd=lwd)
			return(out)

		scale_startx = xoffset

		out += render_points(scale_startx, y, scale_break, 0, break_time)
		out += render_points(scale_startx+scale_break+scale_gap, y, scale_width - scale_gap - scale_break, 24, max(maxtime, 36))
		y += ypadding/2

		out += render_scale(scale_startx, y, scale_break, scale_height, 0, break_time, range(0, int(break_time), 2))
		out += render_scale(scale_startx+scale_break+scale_gap, y, scale_width - scale_gap - scale_break, scale_height, 24, max(maxtime, 36), [i*24 for i in range(1, int(maxtime/24+1))])
	return([out, lineheight*4 +ypadding])


def add_output(old, new):
	return([o+n for o, n in zip(old, new)])


def render_periods(periods, x, y, caption, height, render_function, metrics, style, dashes=False, **kwargs):

	daywidth_function= metrics[0]
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	w = [period_width(i, daywidth_function) for i in periods]
	first = True
	last = False
	out = ""
	for p in periods:
		if p==periods[-1]:
			last=True
		[svg_out, y_out] = render_function(p, caption, x, y, height, metrics, style, first_pass=first, **kwargs)
		out += svg_out
		if dashes and not last:
			out += svg_line(x+period_width(p, daywidth_function), y+height/2, x+period_width(p, daywidth_function)+periodspacing, y+height/2, lwd=lwd)
		x += period_width(p, daywidth_function) + periodspacing
		first=False
	return([out, y_out])


########################################
########################################
########################################

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("file")
@click.option("--output", "-o", type=str, default="", help='Output file name. Default: INPUT.svg')
@click.option("--fontsize", "-s", type=int, default=14, help='Output font size (default 11)')
@click.option("--font", "-f", type=str, default="Arial", help='Output font type (default: Arial)')
@click.option("--padding", "-p", type=float, default=1, help='Y-axis padding factor (default 1)')
@click.option("--condensed", "-c", is_flag=True, help='Show condensed daygrid')
@click.option("--timescale", "-t", is_flag=True, help='Show time scale')
@click.option("--graph", "-g", is_flag=True, help='Show dose graph')
@click.option("--ellipsis", "-e", is_flag=True, help='Reduce symbols in condensed output')
@click.option("--all", "-A", is_flag=True, help='All options, equivalent to -ctge')
@click.option("--debug", "-d", is_flag=True, help='Debug output')
def main(file, debug, fontsize, output, font, condensed, timescale, padding, ellipsis, graph, all):
	"""Clinical Trial design visualization


	Generates a 'schedule of assessments' overview figure based on a json-formatted input FILE (see examples for guidance). Graphical output is provided in svg vector format that can be rendered by any webbrowser or directly imported into Office applications. Use below OPTIONS to manage the output style.
	

	Version 2.0 (Dec-2021),	proudly written in functional Python by Rainer Strotmann"""

	if all:
		condensed=True
		timescale=True
		graph=True
		ellipsis=True

	infile = pathlib.Path(file)
	inpath = pathlib.Path(file).resolve().parent
	if output:
		outfile = inpath.joinpath(output)
	else:
		outfile = inpath.joinpath(infile.stem + ".svg")

	ypadding = fontsize/1.8 * padding

	canvas = cairo.Context(cairo.SVGSurface("temp.svg", 10, 10))
	canvas.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(fontsize)

	try:
		with open(infile) as f:
			td = json.load(f)
	except json.decoder.JSONDecodeError as err:
		print(f'Json syntax error in input file {infile}:\n{err}')
		sys.exit()
	except:
		print("Error loading input file")
		sys.exit()

	periods = []

	if "periods" in td.keys():
		for p in td["periods"]:
			try:
				assert_period_format(p)
			except TypeError as err:
				print(f'Syntax error in period {p["caption"]}: {err}')
			periods.append(p)

	if "cycles" in td.keys():
		for c in td["cycles"]:
			c["start"] = 1
			try:
				assert_period_format(c)
			except TypeError as err:
				print(f'Syntax error in cycle {p["caption"]}: {err}')
			periods.append(c)

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

	periodspacing = textwidth_function("XX")
	lineheight = textheight_function("X") * 2
	xoffset = max([textwidth_function(i) for i in item_names(td, 'procedures') + item_names(td, 'intervals') + item_names(td, 'admininstrations')]) + 30
	yoffset = 10
	lwd = fontsize/10

	style = (periodspacing, lineheight, ypadding, lwd, ellipsis, debug)

	## rendering:
	out = ["", yoffset]

	# render header
	out = add_output(out, render_periods(periods, xoffset, out[1], "", lineheight, render_periodcaption, metrics, style))

	try:
		out = add_output(out, render_periods(periods, xoffset, out[1], "", lineheight, render_daygrid, metrics, style, dashes=True))
	except Exception as err:
		print(f'error rendering daygrid: {err}')

	# render intervals, administrations, procedures
	for n in item_names(td, 'intervals'):
		try:
			out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_interval, metrics, style))
		except Exception as err:
			raise IndexError(f'error rendering intervals: {err}')

	for n in item_names(td, 'administrations'):
		out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_procedure, metrics, style, default_symbol="arrow"))

		if graph:
			if [i for p in periods for i in extract_doses(p, n) if i != ""]:
				out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_dose_graph, metrics, style))

	for n in item_names(td, 'procedures'):
		out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_procedure, metrics, style, default_symbol="diamond"))

		# test whether to render timescale. Only the first period matters
		if timescale:
			ts = False
			x = xoffset
			for p in periods:
				if has_timescale(p, n):
					ts = True
					break
				x += period_width(p, daywidth_function)
				x += periodspacing
			if ts:
				out = add_output(out, render_times(p, n, x, out[1], lineheight, metrics, style, maxwidth=xoffset + sum([period_width(i, daywidth_function) for i in periods]) + (len(periods)-1) * periodspacing))

	# re-calculate image dimensions, finalize svg
	viewport_width = xoffset + sum([period_width(i, daywidth_function) for i in periods]) + (len(periods)) * periodspacing
	viewport_height = out[1]

	svg_out = f'<svg width="{viewport_width}" height="{viewport_height}" xmlns="http://www.w3.org/2000/svg">\n<style>text {{font-family: {font}; font-size: {fontsize}px ;}}</style>\n<desc>Trial design autogenerated by td.py V2.0 (Dec-2021), author: Rainer Strotmann</desc><title>{infile.stem}</title>' + out[0]
	svg_out += f'</svg>'

	with open(outfile, "w") as f:
		f.write(svg_out)
	return


if __name__ == "__main__":
	main()