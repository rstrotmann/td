#!/opt/homebrew/bin/python3

from ensurepip import version
from tokenize import Double
import typer
import pathlib
import cairo
import json
import re
import sys


### GLOBAL VARIABLES
__version__ = "2.1"
__date__ = "Jan-2022"
debug = False


def assert_period_format(period):
	"""assert minimum required fields are present in period
	"""
	try:
		assert "caption" in period.keys()
		assert "duration" in period.keys() and type(period["duration"])==int
	except AssertionError as err:
		raise AssertionError(f'missing required fields (caption and duration) in period {period}')
	return


def assert_procedure_format(procedure):
	"""assert minimum required fields are present in procedure
	"""
	try:
		assert "caption" in procedure.keys()
		assert "days" in procedure.keys()
	except:
		raise AssertionError(f'missing required fields (caption and days) in procedure {procedure}')
	return


def assert_interval_format(interval):
	"""assert minimum required fields are present in interval
	"""
	try:
		assert "caption" in interval.keys()
		assert ("start" in interval.keys() and "duration" in interval.keys()) or "days" in interval.keys()
	except AssertionError as err:
		raise AssertionError(f'missing required fields (caption", and either start and duration, or days) in interval {interval}')
	return


def decode_daylist(daylist: list) -> list:
	"""convert 'days' field (including day ranges) to list of individual days

	Convert list of period days given in a flxible format into a well-formed into a list of days. The input can contain either days in numerical format (e.g., -1, 1, 2), or as strings that may represent single days (e.g., "-1", "1") or day ranges (e.g., "1-3") . Day ranges can also include multiple segments (e.g., "1-3, 5-7", "1-3, 4, 5").
	
	:param daylist: input list of numbers and/or strings representing individual days or day ranges (see above)
	:type daylist:	list
	:rtype:			list
	:return:		list of days in strict numerical form
	"""
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


def item_names(periods, item_class):
	"""return a list of interval/administration/procedure names included in a list of periods
	
	:param periods: 	periods to search
	:type periods: 		list of period dictionaries
	:param item_class:	class of items to include, can be 'intervals', 'administrations' or 'procedures'
	:type item_class:	string
	:rtype:				list
	:return:			names of items of the respective type included in the list periods
	"""
	out = []
	for p in periods:
		if item_class in p.keys():
			for proc in p[item_class]:
				try:
					temp = proc['caption']
					if not temp in out:
						out.append(temp)
				except:
					raise KeyError(f'no caption field in item {proc}')
	return(out)


def iterate_over_procedures(period, caption, out, function):
	"""apply a reduce function to all procedures with a given caption
	
	:param period:	period
	:type period: 	dictionary
	:param caption:	procedure caption to select
	:type caption:	string
	:param out:		accumulator start value, mostly a list with length of the period
	:type out:		flexible
	:rtype:			flexible
	:return: 		accumulator out
	"""
	for x in ['intervals', 'administrations', 'procedures']:
		if x in period.keys():
			for proc in period[x]:
				if proc['caption'] == caption:
					function(proc, out)
	return(out)


def extract_procedure(period, caption):
	"""get specified administration/procedure as list of tuples (day, [times], relative) for individual days
	"""
	out = []
	def temp(proc, out):
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
		out += [(d, t, rel) for d in decode_daylist(proc['days'])]
		return(out)
	return(iterate_over_procedures(period, caption, out, temp))


def extract_labels(period, caption):
	out = [""] * period['duration']
	def temp(proc, out):
		if 'labels' in proc.keys():
			if 'days' in proc.keys():
				for d,l in zip(decode_daylist(proc['days']), proc['labels']):
					out[day_index(period, d)] = l
			elif 'start' in proc.keys() and 'duration' in proc.keys():
				out[day_index(period, proc["start"])] = proc['labels'][0]
		return(out)
	return(iterate_over_procedures(period, caption, out, temp))


def extract_footnotes(period, caption):
	"""extract footnotes for procedures by day, if applicable"""
	out = [[False] * period['duration'], [''] * period['duration'], []]
	def temp(proc, out):
		if 'footnotes' in proc.keys():
			for f in proc["footnotes"]:
				if not "days" in f.keys():
					raise KeyError(f'no "days" in footnote "{f["text"]}"')
				else:
					if not isinstance(f["days"], list):
						daylist = [f["days"]]
					else:
						daylist = f["days"]
					for d in decode_daylist(daylist):
						i = day_index(period, d)
						out[0][i] = True
						if out[1][i]:
							out[1][i] += ","
						out[1][i] += str(f['symbol'])
						out[2].append([f['symbol'], f['text']])
		return(out)
	return(iterate_over_procedures(period, caption, out, temp))


def footnote_list(periods):
	cpt = []
	for n in ['intervals', 'administrations', 'procedures']:
		cpt += item_names(periods, n)
	fn = []
	for c in cpt:
		for p in periods:
			f = extract_footnotes(p, c)[2]
			for ff in f:
				if not ff[0] in [i[0] for i in fn] and ff[1] != "":
					fn.append(ff)
	return(sorted(fn))


def extract_start_end(daylist):
	"""from day list, extract start and end days of trains of days"""
	last_day = 0
	out = []
	if daylist:
		daylist.sort()
		for i in daylist:
			if i == daylist[0] or i != last_day+1 and not (last_day == -1 and i == 1):
				out += [last_day, i]
			last_day = i
		out += [i]
	out = list(dict.fromkeys(out))
	if 0 in out:
		out.remove(0)
	return(out)


def activity_days(period):
	"""returns a list of boolean values per day to indicate whether there are procedures on the day"""
	start = period["start"]
	duration = period["duration"]
	if start <0 and start+duration >0:
		duration+=1
	
	# start and end of period, start and end of trains of procedure days
	out = [start, start+duration-1]
	for x in ["administrations", "procedures"]:
		if x in period.keys():
			for i in period[x]:
				if "days" in i.keys():
					temp = decode_daylist(i["days"])
					out += extract_start_end(temp)

	# all PK days
	if "procedures" in period.keys():
		for i in period["procedures"]:
			if "times" in i:
				out += [d for (d, t, r) in normalize_procedure(extract_procedure(period, i["caption"]))]

	if "intervals" in period.keys():
		for i in period["intervals"]:
			if "start" in i.keys() and "duration" in i.keys():
				start = i["start"]
				duration = i["duration"]
				if start <0 and start+duration>0:
					duration += 1
				temp = list(range(start, start+duration))
				if 0 in temp:
					temp.remove(0)
				out += extract_start_end(temp)
	out.sort()
	temp = [False] * period['duration']
	for i in list(dict.fromkeys(out)):
		temp[day_index(period, i)] = True
	return(temp)


def normalize_procedure(procedure):
	"""break down procedure times to subsequent days, if longer than 24 h"""
	out = []
	for (d, t, rel) in procedure:
		dd = 0
		while t:
			temp = [i for i in t if i<24]
			if temp:
				out.append((d+dd, temp, rel))
			t = [i-24 for i in t if i>=24]
			dd += 1
	return(out)


def unnormalize_procedure(procedure):
	""" collate procedure times into single day, if relative to the same day"""
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
	"""test if procedure has timescale in the respective period"""
	out = []
	def temp(proc, out):
		if 'timescale' in proc.keys():
			if proc['timescale'] == 'show':
				out.append(True)
		return(out)
	return(True in iterate_over_procedures(period, caption, out, temp))


def extract_field(period, caption, field):
	out = [""] * period['duration']
	def temp(proc, out):
		val = proc[field] if field in proc.keys() else ""
		for (day, val) in [(d, val) for d in decode_daylist(proc['days'])]:
			out[day_index(period, day)] = val
		return(out)
	return(iterate_over_procedures(period, caption, out, temp))


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
	"""convert day to index within daylist"""
	temp = day - period['start']
	if period['start'] < 0 and day > 0:
		temp -= 1 # correct for absent day 0
	if temp <0 or temp>period["duration"]-1:
		raise IndexError(f'day index {day} out of range ({period["start"]} to {period["start"]+period["duration"]})')
	return(temp)


def day_labels(period):
	temp = [""] * period['duration']
	if "daylabels" in period.keys():
		for i in decode_daylist(period['daylabels']):
			temp[day_index(period, i)] = i
	return(temp)


def day_shadings(period):
	temp = [False] * period['duration']
	if "dayshading" in period.keys():
		for i in decode_daylist(period['dayshading']):
			temp[day_index(period, i)] = True
	return(temp)


###### low-level rendering functions

def svg_line(x1, y1, x2, y2, lwd=1, color="black", dashed=False):
	dash = f'stroke-dasharray: {lwd*3} {lwd*3}' if dashed else ""
	return(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color}; stroke-width:{lwd}; {dash}" />\n')


def svg_rect(x, y, w, h, lwd=1, fill_color="none", line_color="black"):
	return(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" style="stroke:{line_color};  stroke-width:{lwd}; fill:{fill_color};" />\n')


def svg_circle(x, y, r, lwd=1.2, fill_color="none", line_color="black"):
	return(f'<circle cx="{x}" cy="{y}" r="{r}" style="stroke:{line_color};  stroke-width:{lwd}; fill:{fill_color};"/>\n')


def svg_text(x, y, text, css_class=""):
	if css_class:
		return(f'<text x="{x}" y="{y}" class="{css_class}">{text}</text>\n')
	else:
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


def svg_symbol(x, y, width, symbol, size=1, fill=False, fill_color="none", **kwargs):
	if symbol == "diamond":
		return svg_path(x, y, [(0,-0.5), (0.25, 0), (0, 0.5), (-0.25, 0)], size=size*1.4, fill=fill, fill_color=fill_color, **kwargs)
	elif symbol == "block":
		w = width/size/1.5*.7
		return svg_path(x, y, [(w/-2, -.25), (w/2, -.25), (w/2, .25), (-w/2, .25)], size=size*1.5, fill=fill, fill_color=fill_color, **kwargs)
	elif symbol == "arrow":
		return svg_path(x, y, [(-0.03, -0.5), (0.03, -0.5), (0.03, 0), (0.1875, 0), (0.0, 0.5), (-0.1875, 0), (-0.03, 0)], size=size*1.2, fill=True, fill_color="black", **kwargs)
	elif symbol == "circle":
		return svg_circle(x, y, width/2*size, fill_color=fill_color, **kwargs)
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
	out = [""] * (period['duration']+1)
	# out = period_dummy(period, "") + [""]
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
	"""return list of x-coordinates for day starts"""
	out=[xoffset]
	acc = xoffset
	for i in daywidth_function(period):
		acc += i
		out.append(acc)
	return out[:-1]


def period_day_centers(period, xoffset, daywidth_function):
	"""return list of x-coordinates for day centers"""
	return([start + width / 2 for start, width in zip(period_day_starts(period, xoffset, daywidth_function), daywidth_function(period))])


def period_day_ends(period, xoffset, daywidth_function):
	"""return list of x-coordinates for day ends"""
	starts = period_day_starts(period, xoffset, daywidth_function)
	widths = daywidth_function(period)
	return([s+w for s, w in zip(starts, widths)])


####### functions that rely on the metrics

def render_dummy(period, xoffset, yoffset, lineheight, metrics):
	"""render bounding box for visual debugging purposes. Output is svg code only."""
	daywidth_function = metrics[0]
	return(svg_rect(xoffset, yoffset, period_width(period, daywidth_function), lineheight, lwd=0, fill_color="cornsilk"))


def render_daygrid(period, caption, xoffset, yoffset, height, metrics, style, first_pass=True):
	"""render svg output for the day grid for a period. Output is [svg_output, height]"""
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
		if width>textwidth_function(str(label)):
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
	brackets = extract_field(period, caption, "decoration")
	symbols = procedure_symbols(period, caption, default_symbol)
	dlabels = day_labels(period)
	values = extract_field(period, caption, "value")

	ellipses = [1 if (s!="" and l == "" and len(symbols)>3) else 0 for (s,l) in zip(symbols, dlabels)]

	for p, w, s, b, e, v in zip(centers, widths, symbols, brackets, ellipses, values):
		if s:
			if e==1 and b=="" and ellipsis:
				svg_out += svg_circle(p, y, lineheight/30, fill_color="black")
			elif v != "":
				if v == 0:
					svg_out += svg_symbol(p, y, w*.5, "circle", fill=False, fill_color="none", lwd=lwd)
				else:
					svg_out += svg_symbol(p, y, w*.5, "circle", fill=True, fill_color="black")
			else:
				svg_out += svg_symbol(p, y, w, s, size=textheight_function("X"), lwd=lwd, title=caption)
				if b=="bracketed":
					svg_out += svg_open_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=lwd)
					svg_out += svg_close_bracket(p, y, lineheight, w*.8, xpadding=0, radius=lineheight/8, lwd=lwd)
	return([svg_out, lineheight+ypadding])


def render_labels_footnotes(period, caption, xoffset, yoffset, linheight, metrics, style, footnotes=False):
	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	y = yoffset + lineheight - textheight_function("X")/2

	lbl = extract_labels(period, caption)
	has_lbl = True in [i != '' for i in lbl]
	[fnt_days, fnt_symbols, fnt_text] = extract_footnotes(period, caption)	
	has_fnt = True in fnt_days
	if not footnotes:
		has_fnt = False

	svg_out = ""

	if has_lbl or has_fnt:
		if debug:
			svg_out += render_dummy(period, xoffset, yoffset, lineheight, metrics)

		centers = period_day_centers(period, xoffset, daywidth_function)
		widths = daywidth_function(period)
		for l, c, w, fd, fs in zip(lbl, centers, widths, fnt_days, fnt_symbols):
			temp = str(l)
			if fd and footnotes:
				temp += f' ({fs})'
			svg_out += svg_text(c-textwidth_function(temp)/2, y, temp)
	return([svg_out, linheight+ypadding])


def make_footnote_text(footnote):
	return(f'({footnote[0]})\t{footnote[1]}')


def render_footnote_text(footnote, x, y, linehight, metrics, style):
	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	svg_out = svg_text(x, y, make_footnote_text(footnote), css_class="footnote")
	return([svg_out, textheight_function("XX")+ypadding])


def render_dose_graph(period, caption, xoffset, yoffset, lineheight, metrics, style, first_pass=True):
	"""render dose over time for administration. Output is [svg_output, height]"""
	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	svg_out = ""
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, lineheight+ textheight_function("X"), metrics)

	startx = period_day_starts(period, xoffset, daywidth_function)
	endx = period_day_ends(period, xoffset, daywidth_function)
	doses = [i for i in extract_field(period, caption, "dose")]
	doses_num = [i for i in doses if isinstance(i, int) or isinstance(i, float)]
	if len(doses_num):
		maxdose, mindose = max(doses_num), min(doses_num)
		def dosey(dose):
			return(yoffset + lineheight*0.6 - (dose-mindose)/(maxdose-mindose)*lineheight*0.6)
		# if doses:
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
	y = yoffset + lineheight/2
	if debug:
		svg_out += render_dummy(period, xoffset, yoffset, lineheight, metrics)

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
				if "start" in intv.keys() and "duration" in intv.keys():
					start_list, duration_list = [intv['start']], [intv['duration']]
				elif "days" in intv.keys() and isinstance(intv["days"], list):
					start_list = decode_daylist(intv["days"])
					duration_list = [1 for i in decode_daylist(intv["days"])]
				else:
					raise TypeError(f'{period["caption"]}, interval "{intv["caption"]}"')

				for start, duration in zip(start_list, duration_list):
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


def timescale_height(lineheight, metrics, style):
	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style
	bracket_h = lineheight * 2/3
	timescale_h = lineheight * 1.33 + ypadding * 2
	return(bracket_h + ypadding * 1.5 + timescale_h + ypadding * 2)


def render_times(period, caption, xoffset, yoffset, lineheight, metrics, style, maxwidth=100):
	"""render timescale for procedure. Output is [svg_output, height]"""
	(daywidth_function, textwidth_function, textheight_function) = metrics
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	out = ""
	proc = normalize_procedure(extract_procedure(period, caption))

	ts_days = []
	for x in ['procedures', 'administrations']:
		if x in period.keys():
			for p in period[x]:
				if p['caption'] == caption:
					if "timescale" in p.keys() and p["timescale"]=="show":
						ts_days.append(p["relative"])
	ts_days = set(ts_days)

	y = yoffset
	bracketheight = lineheight * 2/3

	last_scale_end = 0
	if ts_days:
		## curly brackets
		if debug:
			out += render_dummy(period, xoffset, y, bracketheight, metrics)

		for ts_d in ts_days:
			times = unnormalize_procedure([i for i in proc if i[2]==ts_d])[0][1]
			startx = period_day_starts(period, xoffset, daywidth_function)[day_index(period, min([i for (i, t, rel) in proc if rel==ts_d]))]
			endx = period_day_ends(period, xoffset, daywidth_function)[day_index(period, max([i for (i, t, rel) in proc if rel==ts_d]))]
			radius = bracketheight/2
			if radius * 4 > endx-startx:
				startx -= radius/2
				endx += radius/2
				radius = (endx-startx)/5
			out += svg_curly_up(startx, endx, y, radius=radius, lwd=lwd)			
		y += bracketheight + ypadding*1.5

		## timescales
		if debug:
			out += render_dummy(period, xoffset, y, lineheight*1.33 + ypadding*2 + textheight_function("X"), metrics)
		for ts_d in ts_days:
			times = unnormalize_procedure([i for i in proc if i[2]==ts_d])[0][1]

			maxtime = max(times)
			break_time = min(sorted(list([i for i in times if i<24]))[-1] + 2, 23)
			times_below = len([i for i in times if i<=break_time])
			times_above = len([i for i in times if i>break_time])

			startx = period_day_starts(period, xoffset, daywidth_function)[day_index(period, min([i for (i, t, rel) in proc if rel==ts_d]))]

			### scale
			scale_height = lineheight/3
			scale_width = min(len(times) * textwidth_function("XX"), maxwidth-xoffset)
			scale_break = scale_width * times_below/(times_below+times_above)
			scale_gap = textwidth_function("m")

			scale_startx = max(min(startx, xoffset + period_width(period, daywidth_function) - scale_width), xoffset)
			if scale_startx < last_scale_end:
				y += lineheight*1.33 + ypadding*3 + textheight_function("X")

			def render_scale(x, y, width, height, scale_min, scale_max, scale_labels, show_unit=False):
				out = svg_line(x, y, x+width, y, lwd=lwd)
				label_widths = [textwidth_function(str(i)) for i in scale_labels]
				last_label_end = 0
				final_label_begin = x + width - label_widths[-1]/2
				min_delta = textwidth_function(".")

				for i, wi in zip(scale_labels, label_widths):	
					xi = (i-scale_min) * width/(scale_max-scale_min) + x
					out += svg_line(xi, y-height/2, xi, y+height/2, lwd=lwd)
					dxi = wi/2
					if xi-dxi > last_label_end and xi+dxi < final_label_begin - min_delta:
						out += svg_text(xi-dxi, y+height/2+textheight_function("X")+ypadding, str(i))
						last_label_end = xi+dxi+min_delta
					if i == scale_labels[-1]:
						temp = str(i)
						if show_unit:
							temp += " h"
						out += svg_text(xi-dxi, y+height/2+textheight_function("X")+ypadding, temp)
				return(out)

			def render_points(x, y, width, scale_min, scale_max):
				points = [t for t in times if t>=scale_min and t<=scale_max]
				points_x = [(i-scale_min) * width/(scale_max-scale_min) + x for i in points]
				out = ""
				for p, xi in zip(points, points_x):
					out += svg_symbol(xi, y + lineheight/2, 0, "diamond", size=textheight_function("X"), lwd=lwd)
				return(out)

			out += render_points(scale_startx, y, scale_break, 0, break_time)
			out += render_points(scale_startx+scale_break+scale_gap, y, scale_width - scale_gap - scale_break, 24, max(maxtime, 36))

			out += render_scale(scale_startx, y+lineheight+ypadding, scale_break, scale_height, 0, break_time, range(0, int(break_time), 2))
			if maxtime >=24:
				out += render_scale(scale_startx+scale_break+scale_gap, y+lineheight+ypadding, scale_width - scale_gap - scale_break, scale_height, 24, max(maxtime, 36), [i*24 for i in range(1, int(maxtime/24+1))], show_unit=True)
			last_scale_end = scale_startx + scale_width

		return([out, y+lineheight*1.33 + ypadding*3 + textheight_function("X")-yoffset])


def add_output(old, new):
	"""add output of render functions"""
	return([o+n for o, n in zip(old, new)])


def render_periods(periods, x, y, caption, height, render_function, metrics, style, dashes=False, footnotes=False, **kwargs):
	"""applies rendering function to all periods"""
	daywidth_function= metrics[0]
	(periodspacing, lineheight, ypadding, lwd, ellipsis, debug) = style

	w = [period_width(i, daywidth_function) for i in periods]
	first = True
	last = False
	h = 0
	out = ""

	# render labels, if applicable
	has_labels = len([i for ii in [extract_labels(p, caption) for p in periods] for i in ii if i != '']) != 0
	has_footnotes = True in [i for ii in [extract_footnotes(p, caption)[0] for p in periods] for i in ii]
	if not footnotes:
		has_footnotes = False

	if has_labels or has_footnotes:
		xx = x
		for p in periods:
			[svg_out, y_out] = render_labels_footnotes(p, caption, xx, y, height, metrics, style, footnotes=footnotes)
			out += svg_out
			xx += period_width(p, daywidth_function) + periodspacing
		h += lineheight
		y += h

	# render procedure
	for p in periods:
		if p==periods[-1]:
			last=True

		[svg_out, y_out] = render_function(p, caption, x, y, height, metrics, style, first_pass=first, **kwargs)
		out += svg_out

		if dashes and not last:
			out += svg_line(x+period_width(p, daywidth_function), y+height/2, x+period_width(p, daywidth_function)+periodspacing, y+height/2, lwd=lwd)
		x += period_width(p, daywidth_function) + periodspacing
		first=False
	return(add_output(["", h], [out, y_out]))


def render_td(td, title="", debug=False, fontsize=11, font="Arial", condensed=False, autocompress=False, timescale=False, padding=1, ellipsis=False, footnotes=False, graph=False):
	# VALIDATE INPUT
	
	# parse periods
	periods = []
	try:
		for period_class in ["periods", "cycles"]:
			if period_class in td.keys():
				for p in td[period_class]:
					if period_class == "cycles" and not "start" in p.keys():
						p["start"] = 1
					assert_period_format(p)
					periods.append(p)
		if not len(periods):
			raise KeyError("no period or cycle found in trial design")
	except Exception as err:
		raise RuntimeError(f'error parsing periods: {err}')

	## assert procedure format
	for p in periods:
		for (n, assert_func) in [("intervals", assert_interval_format), ("administrations", assert_procedure_format), ("procedures", assert_procedure_format)]:
			if n in p.keys():
				for i in p[n]:
					assert_func(i)

	# MAKE METRICS
	ypadding = fontsize/1.8 * padding
	canvas = cairo.Context(cairo.SVGSurface("temp.svg", 10, 10))
	canvas.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(fontsize)

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
		elif autocompress:
			def daywidth_function(period):
				temp = [textwidth_function("XX") if i else textwidth_function("XX")/3 for i in activity_days(period)]
				return(temp)
		else:
			def daywidth_function(period):
				return([textwidth_function("XX")] * period['duration'])
		return(daywidth_function)

	daywidth_function = make_daywidth_function(textwidth_function, condensed)
	metrics = (daywidth_function, textwidth_function, textheight_function)

	# MAKE STYLE
	periodspacing = textwidth_function("XX")
	lineheight = textheight_function("X") * 2

	try:
		xoffset = 30
		yoffset = 10
		items = item_names(periods, 'procedures') + item_names(periods, 'intervals') + item_names(periods, 'administrations')
		if items:
			xoffset += max([textwidth_function(i) for i in items])
		lwd = fontsize/10
		style = (periodspacing, lineheight, ypadding, lwd, ellipsis, debug)
	except Exception as err:
		raise RuntimeError(f'error making style: {err}')

	# RENDER SVG OUTPUT
	out = ["", yoffset]

	# render header
	out = add_output(out, render_periods(periods, xoffset, out[1], "", lineheight, render_periodcaption, metrics, style))
	try:
		out = add_output(out, render_periods(periods, xoffset, out[1], "", lineheight, render_daygrid, metrics, style, dashes=True))
	except Exception as err:
		raise  RuntimeError(f'error rendering period headers: {err}')

	# render intervals
	for n in item_names(periods, 'intervals'):
		try:
			out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_interval, metrics, style, footnotes=footnotes))
		except Exception as err:
			raise RuntimeError(f'error rendering intervals: {err}')

	# render administrations
	for n in item_names(periods, 'administrations'):
		try:	
			out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_procedure, metrics, style, default_symbol="arrow", footnotes=footnotes))
			if graph:
				if [i for p in periods for i in extract_field(p, n, "dose") if i != ""]:
					out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_dose_graph, metrics, style))
		except Exception as err:
			raise RuntimeError(f'error rendering administrations: {err}')

	# render procedures
	last_proc_has_timescale = False
	for n in item_names(periods, 'procedures'):
		try:
			out = add_output(out, render_periods(periods, xoffset, out[1], n, lineheight, render_procedure, metrics, style, default_symbol="diamond", footnotes=footnotes))
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
					if n == item_names(periods, 'procedures')[-1]:
						last_proc_has_timescale = True
					out = add_output(out, render_times(p, n, x, out[1], lineheight, metrics, style, maxwidth=xoffset + sum([period_width(i, daywidth_function) for i in periods]) + (len(periods)-1) * periodspacing))
		except Exception as err:
			raise RuntimeError(f'error rendering procedures: {err}')

	# apply period decorations
	try:
		x = xoffset
		height = out[1] - yoffset - ypadding/2
		if last_proc_has_timescale:
			height -= timescale_height(lineheight, metrics, style)
		if "periods" in td.keys():
			for p in td["periods"]:
				if "decoration" in p.keys():
					if p["decoration"] == "highlighted":
						out[0] = svg_rect(x-periodspacing/4, yoffset, period_width(p, daywidth_function)+periodspacing/2, height, lwd=0, fill_color="#eee") + out[0]
					if p["decoration"] == "bracketed":
						temp = svg_open_bracket(x-periodspacing/4, yoffset+height/2, height, lineheight/4, xpadding=0, radius=lineheight/4, lwd=lwd)
						temp += svg_close_bracket(x+period_width(p, daywidth_function)+periodspacing/4, yoffset+height/2, height, lineheight/4, xpadding=0, radius=lineheight/4, lwd=lwd)
						out[0] = temp + out[0]
				x += period_width(p, daywidth_function) + periodspacing
	except Exception as err:
		raise RuntimeError(f'error rendering period decorations: {err}')

	# make footnote list
	try:
		max_footnote_width = 0
		fn = footnote_list(periods)
		if footnotes and fn:
			out[1] += ypadding * 4
			for ff in fn:
				out = add_output(out, render_footnote_text(ff, xoffset, out[1], lineheight, metrics, style))
			max_footnote_width = max([textwidth_function(make_footnote_text(ff)) for ff in fn])
	except Exception as err:
		raise RuntimeError(f'error rendering footnote list: {err}')

	# re-calculate overall output dimensions, finalize svg
	viewport_width = max(xoffset + sum([period_width(i, daywidth_function) for i in periods]) + (len(periods)) * periodspacing, xoffset + max_footnote_width)
	viewport_height = out[1]

	svg_out = f'<svg width="{viewport_width}" height="{viewport_height}" xmlns="http://www.w3.org/2000/svg">\n<style>text {{font-family: {font}; font-size: {fontsize}px ;}}</style>\n<desc>Trial design autogenerated by td.py version {__version__} ({__date__}), author: Rainer Strotmann</desc><title>{title}</title>' + out[0]
	
	svg_out += f'</svg>'
	return(svg_out)


########################################

app = typer.Typer(add_completion=False)

def version_callback(value: bool):
    if value:
        typer.echo(f'td version {__version__} ({__date__})')
        raise typer.Exit()

@app.command()
def main(
	file: str = typer.Argument(...),
	#debug: bool = typer.Option(False, "--debug", "-d", help="Debug output"),
	output: str = typer.Option("", "--output", "-o", help="Output file name"),
	font: str = typer.Option("Arial", "--font", "-f", help="Font type"),
	fontsize: int = typer.Option(14, "--fontsize", "-s", help="Font size"),
	padding: float = typer.Option(1, "--padding", "-p", help="Y-axis padding factor"),
	condensed: bool = typer.Option(False, "--condensed", "-c", help="Show condensed daygrid"),
	ellipsis: bool = typer.Option(False, "--ellipsis", "-e", help="Reduce symbols in condensed output"),
	timescale: bool = typer.Option(False, "--timescale", "-t", help="Show time scale"),
	graph: bool = typer.Option(False, "--graph", "-g", help="Show dose graph"),
	footnotes: bool = typer.Option(False, "--footnotes", "-n", help="Show footnotes"),
	all: bool = typer.Option(False, "--all", "-A", help="All options, equivalent to -ctgen"),
	autocompress: bool = typer.Option(False, "--autocompress", "-a", help="Automatically compress daygrid"),
	version: bool = typer.Option(False, "--version", help="Show version and exit", callback=version_callback)
	):
	"""Clinical trial design visualization


	Generates a 'schedule of assessments' overview for clinical trials, based on a json-formatted input FILE. Graphical output is provided in svg vector format that can be rendered by any webbrowser or directly imported into Office applications. Use below OPTIONS to manage the output style.
	

	Version 2.1, proudly written in functional Python (Rainer Strotmann, Jan-2022)
	"""
	if version:
		sys.exit(__version__)

	if all:
		condensed=True
		timescale=True
		graph=True
		ellipsis=True
		footnotes=True

	# read input file
	infile = pathlib.Path(file)
	inpath = pathlib.Path(file).resolve().parent
	if output:
		outfile = inpath.joinpath(output)
	else:
		outfile = inpath.joinpath(infile.stem + ".svg")
	try:
		with open(infile) as f:
			td = json.load(f)
	except json.decoder.JSONDecodeError as err:
		sys.exit(f'Json syntax error in input file {infile}:\n{err}')
	except:
		sys.exit("Error loading input file")

	try:
		svg_out = render_td(td, title=infile.stem, debug=debug, fontsize=fontsize, font=font, condensed=condensed, autocompress=autocompress, timescale=timescale, padding=padding, ellipsis=ellipsis, footnotes=footnotes, graph=graph)
	except Exception as err:
		sys.exit(err)

	with open(outfile, "w") as f:
		f.write(svg_out)
	return




if __name__ == "__main__":
	app()

