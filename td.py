#!/usr/local/bin/python3

import drawSvg as draw
import json


#############################
#	trial period class
#############################

class trialperiod(object):
	def __init__(self, period_dict=dict()):
		self.period = period_dict

	def draw(self, canvas, xoffset=10, yoffset=0, daywidth=20, dayheight=30):
		x = xoffset
		y = yoffset
		for i in range(1, self.period["length"]+1):
			#print(i)
			r = draw.Rectangle(x, y, daywidth, dayheight, fill='none', stroke="black", stroke_width=2)
			canvas.append(r)
			text = str(i)
			canvas.append(draw.Text(text, 8, x,y, fill='black'))
			x += daywidth
		return canvas


#############################
#	trial design class
#############################

class trialdesign(object):
	def __init__(self, js=dict()):
		self.structure = js

	def __str__(self):
		return(json.dumps(self.structure, indent=2))



with open("/Users/rainerstrotmann/Documents/Programming/Python3/trialdesign/test.json") as f:
	#temp = f.read()
	#print(temp)
	#
	temp = json.load(f)
	td = trialdesign(js=temp)
	#print(td)
	canvas = draw.Drawing(1000, 200, displayInline=False)

	for p in td.structure["periods"]:
		print(p["caption"])
		pp = trialperiod(p)
		pp.draw(canvas)
	canvas.saveSvg('example.svg')








# d = draw.Drawing(200, 100, origin='center', displayInline=False)



# # Draw an irregular polygon
# d.append(draw.Lines(-80, -45,
#                     70, -49,
#                     95, 49,
#                     -90, 40,
#                     close=False,
#             fill='#eeee00',
#             stroke='black'))

# # Draw a rectangle
# r = draw.Rectangle(-80,0,40,50, fill='#1248ff')
# r.appendTitle("Our first rectangle")  # Add a tooltip
# d.append(r)

# # Draw a circle
# d.append(draw.Circle(-40, -10, 30,
#             fill='red', stroke_width=2, stroke='black'))

# # Draw an arbitrary path (a triangle in this case)
# p = draw.Path(stroke_width=2, stroke='lime',
#               fill='black', fill_opacity=0.2)
# p.M(-10, 20)  # Start path at point (-10, 20)
# p.C(30, -10, 30, 50, 70, 20)  # Draw a curve to (70, 20)
# d.append(p)

# # Draw text
# d.append(draw.Text('Basic text', 8, -10, 35, fill='blue'))  # Text with font size 8
# d.append(draw.Text('Path text', 8, path=p, text_anchor='start', valign='middle'))
# d.append(draw.Text(['Multi-line', 'text'], 8, path=p, text_anchor='end'))

# # Draw multiple circular arcs
# d.append(draw.ArcLine(60,-20,20,60,270,
#             stroke='red', stroke_width=5, fill='red', fill_opacity=0.2))
# d.append(draw.Arc(60,-20,20,60,270,cw=False,
#             stroke='green', stroke_width=3, fill='none'))
# d.append(draw.Arc(60,-20,20,270,60,cw=True,
#             stroke='blue', stroke_width=1, fill='black', fill_opacity=0.3))

# # Draw arrows
# arrow = draw.Marker(-0.1, -0.5, 0.9, 0.5, scale=4, orient='auto')
# arrow.append(draw.Lines(-0.1, -0.5, -0.1, 0.5, 0.9, 0, fill='red', close=True))
# p = draw.Path(stroke='red', stroke_width=2, fill='none',
#               marker_end=arrow)  # Add an arrow to the end of a path
# p.M(20, -40).L(20, -27).L(0, -20)  # Chain multiple path operations
# d.append(p)
# d.append(draw.Line(30, -20, 0, -10,
#             stroke='red', stroke_width=2, fill='none',
#             marker_end=arrow))  # Add an arrow to the end of a line

# d.setPixelScale(2)  # Set number of pixels per geometry unit
# #d.setRenderSize(400,200)  # Alternative to setPixelScale
# d.saveSvg('example.svg')
# d.savePng('example.png')

# # Display in Jupyter notebook
# d.rasterize()  # Display as PNG
# d  # Display as SVG

