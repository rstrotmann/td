#!/usr/local/bin/python3

import click
import pathlib
import cairo
import json
import random
import math
import re

# def safe_draw(func):
# 	def wrapper(*args , **kwargs):


def draw_safe(f):
	def wrapper(canvas, *args, **kwargs):
		canvas.save()
		canvas.set_line_width(1.2)
		canvas.set_line_join(cairo.LINE_JOIN_ROUND)
		canvas.set_line_join(cairo.LINE_CAP_ROUND)
		canvas.set_source_rgb(0, 0, 0)
		canvas.set_source_rgb(100, 0, 0)
		print("header")
		f(canvas, *args, **kwargs)
		canvas.stroke()
		canvas.restore()
		print("footer")
	return wrapper


def temp_circle(canvas, x, y, height, width, fill=False, ypadding=7):
	def circle(canvas, x, y, width, fill=False):
		size = 0.6
		canvas.arc(x, y, width/2*size, 0, 2*math.pi)
		if fill:
			canvas.fill()

	#def circle(canvas, x, y, height, width):

circle = draw_safe(temp_circle)



class Periodelement(object):
	def __init__(self, properties=dict(), width=15):
		self._properties = properties
		self._width = width
		try:
			self._caption = properties["caption"]
		except ValueError:
			print("Periodelement has no caption!")

	@property
	def width(self):
		return self._width

	def draw_dummy(self, canvas, x, y, height, ypadding=7):
		canvas.save()
		canvas.set_source_rgb(random.uniform(0.8, 1), random.uniform(0.8, 1), random.uniform(0.8, 1))
		canvas.rectangle(x, y, self.width, height+ypadding*2)
		canvas.fill()
		canvas.restore()

	def draw_symbol(self, canvas, f):
		canvas.save()
		canvas.set_line_width(1.2)
		canvas.set_line_join(cairo.LINE_JOIN_ROUND)
		canvas.set_line_join(cairo.LINE_CAP_ROUND)
		canvas.set_source_rgb(0, 0, 0)
		canvas.set_source_rgb(100, 0, 0)
		f
		canvas.stroke()
		canvas.restore()

	def draw_diamond(self, canvas, x, y, height, width, ypadding=7, size=0.6):
		def diamond(canvas, x, y, height, size=size):
			canvas.move_to(x, y-height/2*size)
			canvas.line_to(x + height*1/4*size, y)
			canvas.line_to(x, y+height/2*size)
			canvas.line_to(x - height*1/4*size, y)
			canvas.line_to(x, y-height/2*size)
		self.draw_symbol(canvas, diamond(canvas, x, y, height))

	def draw_circle(self, canvas, x, y, height, width, fill=False, ypadding=7):
		def circle(canvas, x, y, width, fill=False):
			size = 0.6
			canvas.arc(x, y, width/2*size, 0, 2*math.pi)
			if fill:
				canvas.fill()
		self.draw_symbol(canvas, circle(canvas, x, y, width, fill))

	def draw_arrow(self, canvas, x, y, height, width, ypadding=7, size=0.8):
		def arrow(canvas, x, y, height, width, size=size):
			canvas.set_line_width(1.4)
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
		self.draw_symbol(canvas, arrow(canvas, x, y, height, width, size))

def main():
	surface = cairo.SVGSurface("test.svg", 1000, 700)
	canvas = cairo.Context(surface)
	canvas.select_font_face("Helvetica", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(10)

	pe = Periodelement(properties={"caption":"test"})
	# pe.draw_dummy(canvas, 10, 10, 15)
	# pe.draw_diamond(canvas, 10, 10, 20, 15)
	# pe.draw_circle(canvas, 20, 10, 20, 15, fill=True)
	# pe.draw_arrow(canvas, 40, 10, 20, 15)

	circle(canvas, 50, 50, 20, 20)
	surface.finish()

if __name__ == "__main__":
	main()
