"""
Simple Touchscreen Test

Creates a 2x3 grid of test areas. Each area shows a target spot
that is randomized each run. Tap the spot to turn it green. When
all six spots are pressed the test completes.

Run: python Touchscreentest.py
"""

import tkinter as tk
from tkinter import messagebox
import random
import math
import os
import sys


class TouchSection:
	"""Handles one section with selectable pattern modes:
	mode 0: single press spot
	mode 1: diagonal drag (start->end)
	mode 2: X pattern (two diagonal strokes)
	mode 3: corners + center taps (5 targets)
	mode 4: draw a circle
	mode 5: zigzag taps in sequence
	"""
	def __init__(self, parent, width, height, index, on_complete, mode=0):
		self.parent = parent
		# initial logical size (will be updated on Configure)
		self.width = width
		self.height = height
		self.index = index
		self.on_complete = on_complete
		self.mode = mode
		self.canvas = tk.Canvas(parent, width=width, height=height, bg="#111")
		self.canvas.pack(expand=True, fill="both")
		# Ensure targets/layout adjust when the canvas or its parent is resized
		self.canvas.bind("<Configure>", self._on_configure)
		self.target_radius = min(width, height) // 14
		self.items = []
		self.pressed = False
		self.strokes = []  # list of point lists for drawing strokes
		self._draw_border()
		# mouse handlers
		self.canvas.bind("<ButtonPress-1>", self._on_down)
		self.canvas.bind("<B1-Motion>", self._on_move)
		self.canvas.bind("<ButtonRelease-1>", self._on_up)

	def _draw_border(self):
		self.canvas.create_rectangle(2, 2, self.width-2, self.height-2, outline="#2b2b2b")

	def randomize_target(self):
		# update current logical size from actual canvas size
		try:
			w = int(self.canvas.winfo_width() or self.width)
			h = int(self.canvas.winfo_height() or self.height)
			self.width = max(1, w)
			self.height = max(1, h)
		except Exception:
			# fallback to stored values
			pass
		self.pressed = False
		self.strokes.clear()
		for it in list(self.items):
			try: self.canvas.delete(it)
			except Exception: pass
		self.items.clear()
		# recompute target radius based on current size
		self.target_radius = max(6, min(self.width, self.height) // 14)
		if self.mode == 0:
			# single press spot
			margin = self.target_radius + 10
			x = random.randint(margin, max(margin, self.width - margin))
			y = random.randint(margin, max(margin, self.height - margin))
			self.target_center = (x, y)
			self.items.append(self._draw_circle(x, y, self.target_radius, fill="#d33"))
			self._draw_text("Touch the dot", size=12)
		elif self.mode == 1:
			# diagonal drag: pick TL->BR or TR->BL
			self.diag_lr = random.choice([True, False])
			if self.diag_lr:
				start = (self.target_radius+8, self.target_radius+8)
				end = (self.width-self.target_radius-8, self.height-self.target_radius-8)
			else:
				start = (self.width-self.target_radius-8, self.target_radius+8)
				end = (self.target_radius+8, self.height-self.target_radius-8)
			self.start_pt = start
			self.end_pt = end
			# draw blue endpoints and a faint dashed guideline between them
			self.items.append(self._draw_circle(*start, 8, fill="#4aa3ff"))
			self.items.append(self._draw_circle(*end, 8, fill="#4aa3ff"))
			line = self.canvas.create_line(start[0], start[1], end[0], end[1], fill="#4aa3ff", width=2, dash=(6,8))
			self.items.append(line)
			self._draw_text("Drag diagonally from blue dot to the other blue dot")
		elif self.mode == 2:
			# X: just show corners as hints
			# draw faint diagonal guidelines to indicate the X pattern
			l1 = self.canvas.create_line(8, 8, self.width-8, self.height-8, fill="#888", width=2, dash=(5,6))
			l2 = self.canvas.create_line(self.width-8, 8, 8, self.height-8, fill="#888", width=2, dash=(5,6))
			self.items.append(l1)
			self.items.append(l2)
			# add draggable dots at each end of the diagonals
			pad = 12
			dots = [ (pad, pad), (self.width-pad, pad), (pad, self.height-pad), (self.width-pad, self.height-pad) ]
			for (dx,dy) in dots:
				self.items.append(self._draw_circle(dx, dy, 8, fill="#4aa3ff"))
			self.items.append(self._draw_text("Drag from each blue dot across its diagonal", size=10))
		elif self.mode == 3:
			# corners + center
			coords = [ (self.target_radius+8, self.target_radius+8),
					   (self.width-self.target_radius-8, self.target_radius+8),
					   (self.target_radius+8, self.height-self.target_radius-8),
					   (self.width-self.target_radius-8, self.height-self.target_radius-8),
					   (self.width//2, self.height//2) ]
			self.required_targets = set()
			for i, (x,y) in enumerate(coords):
				item = self._draw_circle(x,y,self.target_radius//2, fill="#d33")
				self.items.append(item)
				# store mapping from item->index via tag
			self._corner_centers = coords
			self._draw_text("Touch all 5 dots", size=11)
		elif self.mode == 4:
			# circle draw — show a faint guide circle to follow
			cx = self.width//2
			cy = self.height//2
			r = min(self.width, self.height)//3
			guide = self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#66c2ff", width=2, dash=(6,6))
			self.items.append(guide)
			self._draw_text("Draw a circle")
		elif self.mode == 5:
			# zigzag: left-right-left-right points (sequence)
			h = self.height
			xs_left = 20 + self.target_radius
			xs_right = self.width - 20 - self.target_radius
			ys = [int(h*0.2), int(h*0.4), int(h*0.6), int(h*0.8)]
			self.zig_points = [(xs_left, ys[0]), (xs_right, ys[1]), (xs_left, ys[2]), (xs_right, ys[3])]
			self.zig_index = 0
			for (x,y) in self.zig_points:
				self.items.append(self._draw_circle(x,y,self.target_radius//2, fill="#d33"))
			self._draw_text("Tap the targets in sequence")

	def _draw_circle(self, x, y, r, fill="#d33"):
		return self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline="#fff", width=2)

	def _draw_text(self, text, size=11):
		# position text relative to current width
		try:
			x = max(10, self.width // 2)
		except Exception:
			x = 100
		return self.canvas.create_text(x, 18, text=text, fill="#cfcfcf", font=(None, size))

	def _on_configure(self, event):
		"""Called when the canvas is resized; update logical size and redraw targets."""
		try:
			new_w = int(event.width)
			new_h = int(event.height)
			if new_w != self.width or new_h != self.height:
				self.width = new_w
				self.height = new_h
				# Re-randomize so targets fill the new area
				self.randomize_target()
		except Exception:
			pass

	# mouse event handling for strokes and taps
	def _on_down(self, event):
		self._current_stroke = [(event.x, event.y)]
		# handle simple taps for modes with targets
		if self.mode in (0,3,5):
			self._handle_tap(event.x, event.y)

	def _on_move(self, event):
		if hasattr(self, '_current_stroke'):
			self._current_stroke.append((event.x, event.y))
			# draw a small line for feedback
			if len(self._current_stroke) >= 2:
				x1,y1 = self._current_stroke[-2]
				x2,y2 = self._current_stroke[-1]
				self.canvas.create_line(x1,y1,x2,y2, fill="#888", width=2, tags=("stroke",))

	def _on_up(self, event):
		if hasattr(self, '_current_stroke'):
			self._current_stroke.append((event.x, event.y))
			self.strokes.append(self._current_stroke)
			stroke = self._current_stroke
			delattr = False
			try:
				del self._current_stroke
			except Exception:
				pass
			# evaluate patterns that use strokes
			if self.mode == 1:
				if self._eval_diag_drag(stroke):
					self._mark_done()
			elif self.mode == 2:
				if self._eval_x_pattern():
					self._mark_done()
			elif self.mode == 4:
				if self._eval_circle():
					self._mark_done()

	def _handle_tap(self, x, y):
		if self.pressed:
			return
		if self.mode == 0:
			cx,cy = self.target_center
			if math.hypot(x-cx, y-cy) <= self.target_radius:
				self.canvas.itemconfigure(self.items[0], fill="#2ecc71")
				self._mark_done()
			else:
				self._flash_miss_item(self.items[0])
		elif self.mode == 3:
			# check which corner target hit
			for i,(cx,cy) in enumerate(self._corner_centers):
				if math.hypot(x-cx, y-cy) <= (self.target_radius//1.5):
					# mark that corner
					item = self.items[i]
					try: self.canvas.itemconfigure(item, fill="#2ecc71")
					except Exception: pass
			# check completion
			all_green = True
			for it in self.items:
				try:
					if self.canvas.itemcget(it, "fill") != "#2ecc71":
						all_green = False
						break
				except Exception:
					all_green = False
			if all_green:
				self._mark_done()
		elif self.mode == 5:
			# require sequential taps on zig points
			if self.zig_index < len(self.zig_points):
				tx,ty = self.zig_points[self.zig_index]
				if math.hypot(x-tx, y-ty) <= self.target_radius:
					# mark item green
					try:
						self.canvas.itemconfigure(self.items[self.zig_index], fill="#2ecc71")
					except Exception:
						pass
					self.zig_index += 1
					if self.zig_index >= len(self.zig_points):
						self._mark_done()
				else:
					self._flash_miss_item(self.items[self.zig_index])

	def _flash_miss_item(self, item):
		try:
			orig = self.canvas.itemcget(item, "fill")
			self.canvas.itemconfigure(item, fill="#ff6b6b")
			self.canvas.after(200, lambda: self.canvas.itemconfigure(item, fill=orig))
		except Exception:
			pass

	def _mark_done(self):
		if self.pressed:
			return
		self.pressed = True
		# visually mark whole section
		try:
			self.canvas.configure(bg="#072017")
		except Exception:
			pass
		try:
			self.on_complete(self.index)
		except Exception:
			pass

	# evaluation helpers
	def _eval_diag_drag(self, stroke):
		if not stroke: return False
		sx,sy = stroke[0]
		ex,ey = stroke[-1]
		# check start near expected start and end near expected end
		def near(a,b,thr=24):
			return math.hypot(a[0]-b[0], a[1]-b[1]) <= thr
		if near((sx,sy), self.start_pt, thr=30) and near((ex,ey), self.end_pt, thr=30):
			return True
		return False

	def _eval_x_pattern(self):
		# require that strokes cover both diagonals roughly
		if len(self.strokes) < 2:
			return False
		covered1 = False
		covered2 = False
		# diagonal lines
		def dist_point_to_line(p, a, b):
			# distance from p to line ab
			ax,ay = a; bx,by = b; px,py = p
			num = abs((by-ay)*px - (bx-ax)*py + bx*ay - by*ax)
			den = math.hypot(by-ay, bx-ax) or 1
			return num/den
		a1=(0,0); b1=(self.width, self.height)
		a2=(self.width,0); b2=(0,self.height)
		for stroke in self.strokes:
			# sample some points
			pts = stroke[::max(1, len(stroke)//8)]
			d1 = sum(dist_point_to_line(p,a1,b1) for p in pts)/len(pts)
			d2 = sum(dist_point_to_line(p,a2,b2) for p in pts)/len(pts)
			if d1 < 30:
				covered1 = True
			if d2 < 30:
				covered2 = True
		return covered1 and covered2

	def _eval_circle(self):
		# combine all stroke points and check for circularity
		pts = [p for stroke in self.strokes for p in stroke]
		if len(pts) < 20:
			return False
		xs = [p[0] for p in pts]
		ys = [p[1] for p in pts]
		cx = sum(xs)/len(xs)
		cy = sum(ys)/len(ys)
		dists = [math.hypot(x-cx,y-cy) for x,y in pts]
		mean_r = sum(dists)/len(dists)
		if mean_r < 20:
			return False
		# require low relative stddev
		var = sum((d-mean_r)**2 for d in dists)/len(dists)
		std = math.sqrt(var)
		if std/mean_r < 0.35:
			# also ensure start/end are close (closed loop)
			s = pts[0]; e = pts[-1]
			if math.hypot(s[0]-e[0], s[1]-e[1]) <= mean_r*0.35:
				return True
		return False


class TouchscreenTestApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Touchscreen Test — 6 Sections")
		self.sections = []
		self.completed = set()

		header = tk.Frame(root, bg="#0b0b0b")
		header.pack(fill="x")
		tk.Label(header, text="Touchscreen Test", fg="#f5f5f5", bg="#0b0b0b", font=(None, 18, "bold")).pack(side="left", padx=12, pady=8)
		self.status_lbl = tk.Label(header, text="0 / 6", fg="#d0d0d0", bg="#0b0b0b", font=(None, 12))
		self.status_lbl.pack(side="right", padx=12)

		# Grid container
		grid = tk.Frame(root, bg="#000")
		grid.pack(expand=True, fill="both", padx=8, pady=8)

		rows, cols = 2, 3
		cell_w, cell_h = 360, 320

		# assign modes for each of the six sections as requested
		# 0: press, 1: diagonal drag, 2: X, 3: corners+center, 4: circle, 5: zigzag
		modes = [0, 1, 2, 3, 4, 5]

		for r in range(rows):
			for c in range(cols):
				frame = tk.Frame(grid, width=cell_w, height=cell_h, bg="#0a0a0a")
				frame.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
				grid.grid_rowconfigure(r, weight=1)
				grid.grid_columnconfigure(c, weight=1)
				idx = r * cols + c
				mode = modes[idx]
				sec = TouchSection(frame, cell_w, cell_h, idx, self._section_completed, mode=mode)
				self.sections.append(sec)

		# Controls
		ctrl = tk.Frame(root, bg="#0b0b0b")
		ctrl.pack(fill="x")
		tk.Button(ctrl, text="Start / Randomize", command=self.start_test, width=16).pack(side="left", padx=8, pady=8)
		tk.Button(ctrl, text="Reset", command=self.reset_test, width=10).pack(side="left", padx=6)
		tk.Button(ctrl, text="Close", command=self.root.destroy, width=8).pack(side="right", padx=8)

		hint = tk.Label(root, text="Tap the red spot in each section. Spots are randomized each run.", fg="#cfcfcf", bg="#000", pady=6)
		hint.pack(fill="x")

		# initialize
		self.start_test()

	def start_test(self):
		self.completed.clear()
		for s in self.sections:
			s.randomize_target()
		self._update_status()

	def reset_test(self):
		self.completed.clear()
		for s in self.sections:
			s.randomize_target()
		self._update_status()

	def _section_completed(self, index):
		self.completed.add(index)
		self._update_status()
		if len(self.completed) >= len(self.sections):
			self._on_all_done()

	def _update_status(self):
		self.status_lbl.configure(text=f"{len(self.completed)} / {len(self.sections)}")

	def _on_all_done(self):
		try:
			messagebox.showinfo("Completed", "All sections pressed — Test complete.")
		except Exception:
			pass


def main():
	root = tk.Tk()
	# start fullscreen; allow Escape to exit fullscreen and F11 to toggle
	root.geometry("1200x760")
	try:
		root.attributes("-fullscreen", True)
	except Exception:
		try:
			root.state('zoomed')
		except Exception:
			pass

	def _toggle_fullscreen(event=None):
		try:
			cur = root.attributes("-fullscreen")
			root.attributes("-fullscreen", not cur)
		except Exception:
			try:
				# fallback: toggle zoomed
				if root.state() == 'normal':
					root.state('zoomed')
				else:
					root.state('normal')
			except Exception:
				pass

	root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
	root.bind("<F11>", _toggle_fullscreen)
	app = TouchscreenTestApp(root)
	try:
		root.mainloop()
	except KeyboardInterrupt:
		try:
			root.destroy()
		except Exception:
			pass


if __name__ == "__main__":
	main()

