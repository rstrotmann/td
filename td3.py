#!/usr/local/bin/python3

import click
import pathlib
import cairo
import json
# import random
# import math
# import re


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
	td.dump()



class Period(object):
	def __init__(self, js=dict()):
		#self._js = js
		self._length = js['length']
		self._start = js['start']
		self._day_width = [0] * self._length
		self._day_labels = [""] * self._length
		temp = [self.day_index(i) for i in js['daylabels']]
		for i in js['daylabels']:
			self._day_labels[self.day_index(i)] = i

	def day_index(self, day):
		temp = day - self._start
		if self._start < 0 and day > 0:
			temp -=1
		return(temp)

	def dump(self):
		print(f'day width: {self._day_width}')
		print(f'day labels: {self._day_labels}')




class Trialdesign(object):
	def __init__(self, js=dict()):
		self._periods = []
		for p in js["periods"]:
			self._periods.append(Period(p))

	def dump(self):
		for p in self._periods:
			p.dump()








if __name__ == "__main__":
	main()