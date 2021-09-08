#!/usr/local/bin/python3

import cairo


with cairo.SVGSurface("test1.svg", 700, 700) as surface:

	context = cairo.Context(surface)
	#context.select_font_face("Courier", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
	context.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	context.set_font_size(12)

	for i in range(1, 7):
		#print(i)
		x = 50 + i*30
		y = 50
		context.rectangle(x, y, 30, 30)

		context.stroke()

		(_x, _y, width, height, dx, dy) = context.text_extents(str(i))
		#print(x, y, width, height)
		context.move_to(x+15-width/2, y+15+height/2)
		context.show_text(str(i))
