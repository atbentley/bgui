from .frame import Frame
from .widget import Widget, BGUI_DEFAULT, BGUI_NO_NORMALIZE, BGUI_MOUSE_CLICK, BGUI_MOUSE_ACTIVE

class Scrollbar(Widget):
	"""Scrollbar widget.
	
	Use the on_scroll to set a callback for when the scrollbar is being scrubbed.
	
	The slider is the componenet that moves, the slot is the track that the slider lies in."""
	theme_section = 'Scrollbar'
	theme_options = {
				'SlotColor1': (0.2, 0.2, 0.2, 1.0),
				'SlotColor2': (0.2, 0.2, 0.2, 1.0),
				'SlotColor3': (0.2, 0.2, 0.2, 1.0),
				'SlotColor4': (0.2, 0.2, 0.2, 1.0),
				'SlotBorderSize': 1,
				'SlotBorderColor': (0, 0, 0, 1),
				'SliderColor1': (0.4, 0.4, 0.4, 1.0),
				'SliderColor2': (0.4, 0.4, 0.4, 1.0),
				'SliderColor3': (0.4, 0.4, 0.4, 1.0),
				'SliderColor4': (0.4, 0.4, 0.4, 1.0),
				'SliderBorderSize': 1,
				'SliderBorderColor': (0, 0, 0, 1)
				}
			
	def __init__(self, parent, name=None, vertical=True, aspect=None, size=[1,1],
				pos=[0,0], sub_theme='', options=BGUI_DEFAULT):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param direction: specify whether the scollbar is to run horizontally or vertically
		:param aspect: constrain the widget size to a specified aspect ratio
		:param size: a tuple containing the width and height
		:param pos: a tuple containing the x and y position
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options

		"""
		Widget.__init__(self, parent, name, aspect, size, pos, sub_theme, options)
		
		self._slot = Frame(self, self.name+'_slot', pos=[0,0])
		self._slot.on_click = self._jump_to_point
		
		self._slider = Frame(self._slot, self.name+'_slider', pos=[0,0])
		self._slider.on_click = self._begin_scroll
		
		self._slot.colors = [
				self.theme['SlotColor1'],
				self.theme['SlotColor2'],
				self.theme['SlotColor3'],
				self.theme['SlotColor4']
				]
				
		self._slider.colors = [
				self.theme['SliderColor1'],
				self.theme['SliderColor2'],
				self.theme['SliderColor3'],
				self.theme['SliderColor4']
				]
			
		self._slot.border_color = self.theme['SlotBorderColor']
		self._slider.border_color = self.theme['SliderBorderColor']
		self._slot.border = self.theme['SlotBorderSize']
		self._slider.border = self.theme['SliderBorderSize']
		
		self.vertical = vertical
		self.is_being_scrolled = False
		self._jump = False
		self._scroll_offset = 0  # how many pixels from the bottom of the slider scrolling started at
		self._change = 0  # how many pixels the slider has moved since last frame
		
		self._on_scroll = None  # callback for when the slider is moving
	
	@property
	def change(self):
		"""The number of pixels the slider has moved since the last frame."""
		return self._change
		
	@property
	def on_scroll(self):
		"""Callback while the slider is being slid."""
		return self._on_scroll
		
	@on_scroll.setter
	def on_scroll(self, on_scroll):
		self._on_scroll = on_scroll
		
	@property
	def slider_size(self):
		"""The width or height of the slider, depends on direction"""
		if self.vertical:
			return self._slider.height
		else:
			return self._slider.width
		
	@slider_size.setter
	def slider_size(self, value):
		if self.vertical:
			self._slider.height = value
		else:
			self._slider.width = value
		
	@property
	def slider_position(self):
		"""Sets the x or y coordinate of the slider, depending on whether it is a horizontal or vertical scrollbar"""
		if self.vertical:
			return self._slider.y
		else:
			return self._slider.x
		
	@slider_position.setter
	def slider_position(self, value):
		if self.vertical:
			self._slider.y = value
		else:
			self._slider.x = value
		
	def _jump_to_point(self, widget):
		# called when the slot is clicked on
		if not self.is_being_scrolled:
			self._jump = True
			self.is_being_scrolled = True
			if self.vertical:
				self._scroll_offset = self._slider._base_height / 2
			else:
				self._scroll_offset = self._slider._base_width / 2

		
	def _begin_scroll(self, widget):
		# called when the slider is clicked on
		self.is_being_scrolled = True
		if self.vertical:
			self._scroll_offset = self.system.cursor_pos[1] - self._slider._base_y
		else:
			self._scroll_offset = self.system.cursor_pos[0] - self._slider._base_x
		
	def _draw(self):	
		# update scrolling
		if self.is_being_scrolled:
			self._jump = False
			if self.system.click_state not in [BGUI_MOUSE_CLICK, BGUI_MOUSE_ACTIVE]:
				self.is_being_scrolled = False
			else:
				if self.vertical:
					# Check the slider has actually moved
					_min = self._base_y
					_max = self._base_y + self._base_height - self._slider._base_height
					actual = self.system.cursor_pos[1] - self._scroll_offset
					change = min(_max, max(actual, _min)) - self._slider._base_y
					if change != 0:
						self._slider.y += change / self._base_height
						if self.options & BGUI_NO_NORMALIZE:
							self._change = change
						else:
							self._change = change / self._base_height

						if self.on_scroll:
							self.on_scroll(self)
					else:
						self._change = 0

				else:
					# Check the slider has actually moved
					_min = self._base_x
					_max = self._base_x + self._base_width - self._slider._base_width
					actual = self.system.cursor_pos[0] - self._scroll_offset
					change = min(_max, max(actual, _min)) - self._slider._base_x
					if change != 0:
						self._slider.x += change / self._base_width
						if self.options & BGUI_NO_NORMALIZE:
							self._change = change
						else:
							self._change = change / self._base_width

						if self.on_scroll:
							self.on_scroll(self)
					else:
						self._change = 0
		else:
			self._change = 0
		
		Widget._draw(self)