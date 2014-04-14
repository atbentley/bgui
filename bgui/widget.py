"""

This module defines the following constants:

*Widget options*
	* BGUI_DEFAULT = 0
	* BGUI_CENTERX = 1
	* BGUI_CENTERY = 2
	* BGUI_NO_NORMALIZE = 4
	* BGUI_NO_THEME = 8
	* BGUI_NO_FOCUS = 16
	* BGUI_CACHE = 32

	* BGUI_CENTERED = BGUI_CENTERX | BGUI_CENTERY

*Widget overflow*
	* BGUI_OVERFLOW_NONE = 0
	* BGUI_OVERFLOW_HIDDEN = 1
	* BGUI_OVERFLOW_REPLACE = 2
	* BGUI_OVERFLOW_CALLBACK = 3

*Mouse event states*
	* BGUI_MOUSE_NONE = 0
	* BGUI_MOUSE_CLICK = 1
	* BGUI_MOUSE_RELEASE = 2
	* BGUI_MOUSE_ACTIVE = 4

.. note::

	The Widget class should not be used directly in a gui, but should instead
	be subclassed to create other widgets.
"""

from collections import OrderedDict
import weakref
import time

# Widget options
BGUI_DEFAULT = 0
BGUI_CENTERX = 1
BGUI_CENTERY = 2
BGUI_NO_NORMALIZE = 4
BGUI_NO_THEME = 8
BGUI_NO_FOCUS = 16
BGUI_CACHE = 32

BGUI_CENTERED = BGUI_CENTERX | BGUI_CENTERY

# Widget overflow
BGUI_OVERFLOW_NONE = 0
BGUI_OVERFLOW_HIDDEN = 1
BGUI_OVERFLOW_REPLACE = 2
BGUI_OVERFLOW_CALLBACK = 3

# Mouse event states
BGUI_MOUSE_NONE = 0
BGUI_MOUSE_CLICK = 1
BGUI_MOUSE_RELEASE = 2
BGUI_MOUSE_ACTIVE = 4


class WeakMethod:
	def __init__(self, f):
		if hasattr(f, "__func__"):
			self.f = f.__func__
			self.c = weakref.ref(f.__self__)
		else:
			self.f = f
			self.c = None

	def __call__(self, *args):
		if self.c == None:
			self.f(*args)
		elif self.c() == None:
			return None
		else:
			self.f(*((self.c(),) + args))


class Animation:
	def __init__(self, widget, attrib, value, time_, callback):
		self.widget = widget
		self.attrib = attrib
		self.prev_value = getattr(widget, attrib)
		self.next_value = value
		self.start_time = self.last_update = time.time()
		self.time = time_
		self.callback = callback

	def update(self):
		if (time.time() - self.start_time) * 1000 >= self.time:
			# We're done, run the callback and
			# return false to let widget know we can be removed
			if self.callback:
				self.callback()
			return False

		dt = (time.time() - self.last_update) * 1000
		self.last_update = time.time()

		dv = ((self.next_value - self.prev_value) / self.time) * dt

		setattr(self.widget, self.attrib, getattr(self.widget, self.attrib) + dv)

		return True


class ArrayAnimation(Animation):
	def __init__(self, widget, attrib, value, time_, callback):
		super().__init__(widget, attrib, value, time_, callback)
		self.prev_value = getattr(widget, attrib)[:]

	def update(self):
		if (time.time() - self.start_time) * 1000 >= self.time:
			# We're done, run the callback and
			# return false to let widget know we can be removed
			if self.callback:
				self.callback()
			return False

		dt = (time.time() - self.last_update) * 1000
		self.last_update = time.time()

		new_value = getattr(self.widget, self.attrib)[:]

		for i in range(len(self.prev_value)):
			dv = ((self.next_value[i] - self.prev_value[i]) / self.time) * dt

			new_value[i] += dv
		setattr(self.widget, self.attrib, new_value)

		return True


class Widget:
	"""The base widget class"""

	theme_section = 'Widget'
	theme_options = {}

	def __init__(self, parent, name=None, aspect=None, size=[0, 0], pos=[0, 0], sub_theme='',
			options=BGUI_DEFAULT):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param aspect: constrain the widget size to a specified aspect ratio
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options
		"""

		if name is None:
			name = "1"
			while name in parent.children:
				name = str(int(name) + 1)

		#: The widget's name
		self.name = name
		self.options = options

		# Store the system so children can access theming data
		self._system = parent._system

		if sub_theme:
			self.theme_section += ':' + sub_theme

		self._generate_theme()

		self._hover = False
		
		#: Whether or not the widget should accept events
		self.frozen = False

		#: Whether or not the widget is visible
		self.visible = True

		# Event callbacks
		self._on_click = None
		self._on_release = None
		self._on_hover = None
		self._on_active = None
		self._on_mouse_enter = None
		self._on_mouse_exit = None

		# Setup the parent
		parent._attach_widget(self)
		self._parent = weakref.proxy(parent)

		# A dictionary to store children widgets
		self._children = OrderedDict()

		#: The widget's z-index. Widget's with a higher z-index are drawn
		#: over those that have a lower z-index
		self.z_index = 0

		# Setup the widget's size and position
		self._width = size[0]
		self._height = size[1]
		if options & BGUI_NO_NORMALIZE:
			if aspect:
				self._base_width = size[1] * aspect
			else:
				self._base_width = size[0]
			self._base_height = size[1]
		else:
			if aspect:
				self._base_width = size[1] * aspect * self.parent._base_height
			else:
				self._base_width = size[0] * self.parent._base_width
			self._base_height = size[1] * self.parent._base_height

		self.x = pos[0]
		self.y = pos[1]

		# A list of running animations
		self.anims = []

	def __del__(self):
		# Debug print
		# print("Deleting", self.name)
		pass

	def _generate_theme(self):
		if isinstance(self.theme_options, set):
			if self.system.theme:
				self.system.theme.warn_legacy(self.theme_section)
			# Legacy theming
			if self.system.theme and not (self.options & BGUI_NO_THEME) and self.theme_section != Widget.theme_section:
				if self.system.theme.supports(self):
					self.theme = self.system.theme
				else:
					self.system.theme.warn_support(self.theme_section)
					self.theme = None
			elif not hasattr(self, "theme"):
				self.theme = None
		else:
			theme = self.system.theme
			theme = theme[self.theme_section] if theme.has_section(self.theme_section) else None

			if theme and not (self.options & BGUI_NO_THEME):
				self.theme = {}

				for k, v in self.theme_options.items():
					if k in theme:
						self.theme[k] = theme[k]
					else:
						self.theme[k] = v
			elif not hasattr(self, "theme"):
				self.theme = self.theme_options

	@property
	def on_click(self):
		"""The widget's on_click callback"""
		return self._on_click

	@on_click.setter
	def on_click(self, value):
		self._on_click = WeakMethod(value)

	@property
	def on_release(self):
		"""The widget's on_release callback"""
		return self._on_release

	@on_release.setter
	def on_release(self, value):
		self._on_release = WeakMethod(value)

	@property
	def on_hover(self):
		"""The widget's on_hover callback"""
		return self._on_hover

	@on_hover.setter
	def on_hover(self, value):
		self._on_hover = WeakMethod(value)

	@property
	def on_mouse_enter(self):
		"""The widget's on_mouse_enter callback"""
		return self._on_mouse_enter

	@on_mouse_enter.setter
	def on_mouse_enter(self, value):
		self._on_mouse_enter = WeakMethod(value)

	@property
	def on_mouse_exit(self):
		"""The widget's on_mouse_exit callback"""
		return self._on_mouse_exit

	@on_mouse_exit.setter
	def on_mouse_exit(self, value):
		self._on_mouse_exit = WeakMethod(value)

	@property
	def on_active(self):
		"""The widget's on_active callback"""
		return self._on_active

	@on_active.setter
	def on_active(self, value):
		self._on_active = WeakMethod(value)

	@property
	def parent(self):
		"""The widget's parent"""
		return self._parent

	@parent.setter
	def parent(self, value):
		self._parent = value
		self._update_position(self._base_size, self._base_value)

	@property
	def system(self):
		"""A reference to the system object"""
		return self._system()

	@property
	def children(self):
		"""The widget's children"""
		return self._children

	@property
	def x(self):
		"""The widget's x position"""
		return self._x

	@x.setter
	def x(self, x):
		self._x = x
		# Make non-normalized
		if not (self.options & BGUI_NO_NORMALIZE):
			x *= self.parent._base_width

		# Make absolute
		if self.parent != self:
			x += self.parent._base_x

		self._base_x = x

		# Update any children
		for widget in self.children.values():
			widget.x = widget._x

	@property
	def y(self):
		"""The widget's y position"""
		return self._y

	@y.setter
	def y(self, y):
		self._y = y
		# Make non-normalized
		if not (self.options & BGUI_NO_NORMALIZE):
			y *= self.parent._base_height

		# Make absolute
		if self.parent != self:
			y += self.parent._base_y

		self._base_y = y

		# Update any children
		for widget in self.children.values():
			widget.y = widget._y

	@property
	def position(self):
		"""The widget's position"""
		return [self._x, self._y]

	@position.setter
	def position(self, value):
		self.x = value[0]
		self.y = value[1]

	@property
	def width(self):
		"""The widget's width"""
		return self._width

	@width.setter
	def width(self, width):
		self._width = width
		# Make non-normalized
		if not (self.options & BGUI_NO_NORMALIZE):
			width *= self.parent._base_width

		self._base_width = width

		for widget in self.children.values():
			widget.width = widget._width

	@property
	def height(self):
		"""The widget's height"""
		return self._height
		
	@height.setter
	def height(self, height):
		self._height = height
		# Make non-normalized
		if not (self.options & BGUI_NO_NORMALIZE):
			height *= self.parent._base_height

		self._base_height = height

		for widget in self.children.values():
			widget.height = widget._height

	@property
	def size(self):
		"""The widget's size"""
		return [self._width, self._height]

	@size.setter
	def size(self, value):
		self.width = value[0]
		self.height = value[1]

	@property
	def _gl_position(self):
	    return [
					[self._base_x, self._base_y],
					[self._base_x + self._base_width, self._base_y],
					[self._base_x + self._base_width, self._base_y + self._base_height],
					[self._base_x, self._base_y + self._base_height]
				]
	

	def move(self, position, time, callback=None):
		"""Move a widget to a new position over a number of frames

		:param positon: The new position
		:param time: The time in milliseconds to take doing the move
		:param callback: An optional callback that is called when he animation is complete
		"""

		self.anims.append(ArrayAnimation(self, "position", position, time, callback))

	def add_animation(self, animation):
		"""Add the animation to the list of currently running animations

		:param animation: The animation
		"""
		self.anims.append(animation)

	def _update_anims(self):
		self.anims[:] = [i for i in self.anims if i.update()]

		for widget in self.children.values():
			widget._update_anims()

	def _handle_mouse(self, pos, event):
		"""Run any event callbacks"""
		# Don't run if we're not visible or frozen
		if not self.visible or self.frozen:
			return

		self._handle_hover()
		if self.on_hover:
			self.on_hover(self)

		if event == BGUI_MOUSE_CLICK:
			self._handle_click()
			if self.on_click:
				self.on_click(self)
		elif event == BGUI_MOUSE_RELEASE:
			self._handle_release()
			if self.on_release:
				self.on_release(self)
		elif event == BGUI_MOUSE_ACTIVE:
			self._handle_active()
			if self.on_active:
				self.on_active(self)

		# Update focus
		if event == BGUI_MOUSE_CLICK and not self.system.lock_focus and not self.options & BGUI_NO_FOCUS:
			self.system.focused_widget = self

		if not self._hover:
			self._handle_mouse_enter()
			if self.on_mouse_enter:
				self.on_mouse_enter(self)
		self._hover = True

		# Run any children callback methods
		for widget in self.children.values():
			if (widget._gl_position[0][0] <= pos[0] <= widget._gl_position[1][0]) and \
				(widget._gl_position[0][1] <= pos[1] <= widget._gl_position[2][1]):
					widget._handle_mouse(pos, event)
			else:
				widget._update_hover(False)

	def _update_hover(self, hover=False):
		if not hover and self._hover:
			self._handle_mouse_exit()
			if self.on_mouse_exit:
				self.on_mouse_exit(self)
		self._hover = hover

		for widget in self.children.values():
			widget._update_hover(hover)

	def _handle_key(self, key, is_shifted):
		"""Handle any keyboard input"""
		for widget in self.children.values():
			if self._hover:
				widget._handle_key(key, is_shifted)

	# These exist so they can be overridden by subclasses
	def _handle_click(self):
		pass

	def _handle_release(self):
		pass

	def _handle_hover(self):
		pass

	def _handle_active(self):
		pass

	def _handle_mouse_enter(self):
		pass

	def _handle_mouse_exit(self):
		pass

	def _attach_widget(self, widget):
		"""Attaches a widget to this widget"""

		if not isinstance(widget, Widget):
			raise TypeError("Expected a Widget object")

		if widget in self.children.values():
			raise ValueError("%s is already attached to this widget" % (widget.name))

		self.children[widget.name] = widget

	def _remove_widget(self, widget):
		"""Removes the widget from this widget's children"""

		del self.children[widget.name]

	def _draw(self):
		"""Draws the widget and the widget's children"""

		# This base class has nothing to draw, so just draw the children

		for child in self.children:
			if self.children[child].visible:
				self.children[child]._draw()
