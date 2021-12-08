#!/usr/local/bin/python3

import click
import cairo

@click.command()
@click.option("--debug", "-d", is_flag=True, help='debug output')
@click.option("--fontsize", "-s", type=int, default=11, help='output font size (default: 11)')
@click.option("--fontface", "-f", type=str, default="Verdana", help='font face (default: Verdana')
def main(debug, fontsize, fontface):
	# Cairo canvas only for text metrics, not for graphics output!
	surface = cairo.SVGSurface("x.svg", 1000, 1000)
	canvas = cairo.Context(surface)
	canvas.select_font_face(fontface, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	canvas.set_font_size(fontsize)

	def textwidth(text):
		(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
		return(cap_width)

	def textheight(text):
		(x, y, cap_width, cap_height, dx, dy) = canvas.text_extents(text)
		return(cap_height)	

	image_pad = 50
	image_size = 1000
	header = f'<svg viewBox="-{image_pad} -{image_pad} {image_size + 2 * image_pad} {image_size + 2 * image_pad}" xmlns="http://www.w3.org/2000/svg">\n'
	footer = f'</svg>'  

	out = header
	out += text_style(fontface, fontsize)
	#out += draw_line(0, 0, 1000, 1000)
	out += draw_rect(0, 0, 1000, 1000)
	text = "Eine längere Zeile zum Testen der Schriftbreite"
	out += draw_text(100, 100, text)

	w = textwidth(text)
	h = textheight(text)
	out += draw_rect(100, 100-h, w, h)

	out += draw_arrow(90, 100, size=fontsize)
	out += footer


	with open("output.svg", "w") as f:
		f.write(out)



def draw_line(x1, y1, x2, y2, lwd=2, color="black"):
	return(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{lwd}" />\n')

def draw_rect(x, y, w, h, lwd=1, color="black"):
	return(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" stroke="{color}" stroke-width="{lwd}" fill-opacity="0" />\n')

def text_style(font, size):
	return(f'<style>text {{font-family: {font}; font-size: {size}px ;}}</style>\n')

def draw_text(x, y, text):
	return(f'<text x="{x}" y="{y}">{text}</text>\n')

def draw_arrow(x, y, size=1):
	#arrow_points = [(-1, 0), (1, 0), (1, 8), (3, 8), (0, 16), (-3, 8), (-1, 8)]
	arrow_points = [(-0.0625, 0.0), (0.0625, 0.0), (0.0625, 0.5), (0.1875, 0.5), (0.0, 1.0), (-0.1875, 0.5), (-0.0625, 0.5)]
	(x1, y1) = arrow_points[-1]
	out = f'<path d="M{x1*size+x} {y1*size+y} '
	for (x2, y2) in arrow_points:
		out += f'L{x2*size+x} {y2*size+x} '
	out += 'Z" />'
	return(out)


if __name__ == "__main__":
	main()