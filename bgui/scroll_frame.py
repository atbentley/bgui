from .gl_utils import *
from .widget import Widget, BGUI_DEFAULT, BGUI_NO_NORMALIZE
from .scrollbar import Scrollbar


class ScrollFrame(Widget):
	"""A frame which manages overflow through clipping and scrollbars"""
	theme_section = 'Frame'
	theme_options = {
				'Color2': (0, 0, 0, 0),
				'Color3': (0, 0, 0, 0),
				'Color1': (0, 0, 0, 0),
				'Color4': (0, 0, 0, 0),
				'BorderSize': 0,
				'BorderColor': (0, 0, 0, 1),
				}

	def __init__(self, parent, name=None, border=None, aspect=None, size=[1, 1], pos=[0, 0],
				sub_theme='', options=BGUI_DEFAULT):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param border: the size of the border around the frame (0 for no border)
		:param aspect: constrain the widget size to a specified aspect ratio
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options

		"""

		Widget.__init__(self, parent, name, aspect, size, pos, sub_theme, options)

		self._aabb_outdated = False
		self._aabb = [
				self._base_x,
				self._base_x + self._base_width,
				self._base_y,
				self._base_y + self._base_height]

		self._vertical_scrollbar = None
		self._horizontal_scrollbar = None
		self._vertical_factor = None

		#: The colors for the four corners of the frame.
		self.colors = [
				self.theme['Color1'],
				self.theme['Color2'],
				self.theme['Color3'],
				self.theme['Color4']
				]

		#: The color of the border around the frame.
		self.border_color = self.theme['BorderColor']
		
		#: The size of the border around the frame.
		self.border = border if border else self.theme['BorderSize']

	def _attach_widget(self, widget):
		Widget._attach_widget(self, widget)
		if widget.name not in [self.name+'_vsb', self.name+'_hsb']:
			self._aabb_outdated = True

	def _remove_widget(self, widget):
		Widget._remove_widget(self, widget)
		if widget.name not in [self.name+'_vsb', self.name+'_hsb']:
			self._aabb_outdated = True

	def determine_bounds(self):
		for child in self.children.values():
			print(child.position[0])
			self._aabb = [
				min(self._aabb[0], child._base_x),  # min x
				max(self._aabb[1], child._base_x + child._base_width),  # max x
				min(self._aabb[2], child._base_y),  # min y
				max(self._aabb[3], child._base_y + child._base_height)]  # max y

		if self._aabb[0] < 0 or self._aabb[1] > self.width:
			# horizontal scrollbar is required
			pass
		else:
			if self._horizontal_scrollbar is not None:
				self._remove_widget(self._horizontal_scrollbar)
				self._horizontal_scrollbar = None

		if self._aabb[2] < 0 or self._aabb[3] > self._base_height:
			# vertical scrollbar is required
			if self._vertical_scrollbar is None:
				width = 10/self._base_width
				self._vertical_scrollbar = Scrollbar(self, self.name+'_vsb', size=[width, 1],
					pos=[1-width, 0])
				self._vertical_scrollbar.slider_size = self._base_height / (self._aabb[3] - self._aabb[2])
				print(self._base_height, self._aabb[3], self._aabb[2], self._aabb[3] - self._aabb[2])
				#self._vertical_scrollbar.slider_size = 0.2
				self._vertical_scrollbar.slider_position = 1 - self._vertical_scrollbar.slider_size
				self._vertical_scrollbar.on_scroll = self._scroll
				self._vertical_factor = self._base_height / (self._aabb[3] - self._aabb[2])
		else:
			if self._vertical_scrollbar is not None:
				self._remove_widget(self._vertical_scrollbar)
				self._vertical_scrollbar = None

	def _scroll(self, scrollbar):
		for child_name in self.children:
			child = self.children[child_name]
			if child in [self._vertical_scrollbar, self._horizontal_scrollbar]:
				continue

			child.y -= scrollbar.change / self._vertical_factor

	def _draw(self):
		"""Draw the frame"""

		if self._aabb_outdated:
			self.determine_bounds()
			self._aabb_outdated = False

		# User scissors to clip
		glBegin(GL_SCISSOR_TEST)
		view = glGetIntegerv(GL_VIEWPORT)
		glScissor(
			int(self.gl_position[0][0] - self.border/2) + view[0],  # x
			int(self.gl_position[0][1] - self.border/2) + view[1],  # y
			int(self.gl_position[1][0] - self.gl_position[0][0] + self.border*2),  # width
			int(self.gl_position[2][1] - self.gl_position[0][1] + self.border*2))  # height

		# Enable alpha blending
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		# Enable polygon offset
		glEnable(GL_POLYGON_OFFSET_FILL)
		glPolygonOffset(1.0, 1.0)

		glBegin(GL_QUADS)
		for i in range(4):
			glColor4f(self.colors[i][0], self.colors[i][1], self.colors[i][2], self.colors[i][3])
			glVertex2f(self.gl_position[i][0], self.gl_position[i][1])
		glEnd()

		glDisable(GL_POLYGON_OFFSET_FILL)

		# Draw an outline
		if self.border > 0:
			# border = self.border/2
			r, g, b, a = self.border_color
			glColor4f(r, g, b, a)
			glPolygonMode(GL_FRONT, GL_LINE)
			glLineWidth(self.border)

			glBegin(GL_QUADS)
			for i in range(4):
				glVertex2f(self.gl_position[i][0], self.gl_position[i][1])

			glEnd()

			glLineWidth(1.0)
			glPolygonMode(GL_FRONT, GL_FILL)

		Widget._draw(self)

		glDisable(GL_SCISSOR_TEST)
