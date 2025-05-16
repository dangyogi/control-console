# templates.py

r'''Various Template subclasses:

# FIX this mess
build a base template
with template(...) as foo:  # also sets Under_construction global var
    foo.a = comp_a(...)          # no foo
    foo.b = comp_b(bar=t.a.foo)  # creates a dynamic reference to foo rather than raise AttributeError
                                 # because we're Under_construction!
    .
    .
    .
    class foo_instance(Instance):
        base = foo

# create an instance of the template
foo_1 = foo_instance(...)
foo_2 = foo_instance(...)

foo_1.draw(...)   # foo_1 passed as parameter, not global variable
'''

#import texture
from context import Instance

class Group(Instance):
    def __init__(self, *components, **kwargs):
        super().__init__(**kwargs)
        if self.trace:
            print(f"Group.__init__: {self.trace=}, {self.get_raw('x_pos')=}, {self.get_raw('y_pos')=} "
                  f"{kwargs=}")
        self.components = components
        for component in components:
            component.template = self
            if hasattr(component, 'name'):
                setattr(self, component.name, component)
    
    def init2(self):
        r'''Sets width and height
        ''' 
        if self.trace:
            print(f"{self}.init2: {self.trace=}, {self.get_raw('x_pos')=}, {self.get_raw('y_pos')=}")
        x_left = 10000000
        x_right = -10000000
        y_upper = 10000000
        y_lower = -10000000
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print("self.init doing component.init", i)
            component.init() 
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print("Group.init getting pos's from component", i)
            xl = component.x_left.i
            if xl < x_left: 
                x_left = xl
            xr = component.x_right.i
            if xr > x_right:
                x_right = xr
            yu = component.y_upper.i
            if yu < y_upper:
                y_upper = yu
            yl = component.y_lower.i
            if yl > y_lower:
                y_lower = yl
        self.width = x_right - x_left + 1
        assert isinstance(self.width, int), f"Group.init got non-integer width {attrs.width}"
        self.height = y_lower - y_upper + 1
        assert isinstance(self.height, int), f"Group.init got non-integer height {attrs.height}"
        if self.trace:
            print(f"Group.init2: {self.trace=}, {self.width=}, {self.height=}")

    def draw2(self):
        if self.trace:
            print(f"{self}.draw2: {self.trace=}, {self.get_raw('x_pos')=}, {self.get_raw('y_pos')=}")
        for i, component in enumerate(self.components, 1):
            if self.trace:
                print("Group.draw doing component draw", i)
            component.draw()


"""
class Icon(context.Template):
    r'''Creates its own render texture and draws its components on it during init().

    Then just draws its texture in draw().

    This is sprite enabled.
    '''
    base = icon_base

    def init(self):
        super().init(template, as_sprite=False)          # sets width and height
        attrs = extend(self, template, **kwargs)        # I'm only the template for my components
        self.texture = texture.Texture("Icon", attrs.width, attrs.height)
        with self.texture.draw_on_texture():
            super().draw(template, **kwargs)
        if attrs.as_sprite:
            self.sprite = sprite.Sprite(self.width, self.height, attrs.dynamic_capture)

    def draw(self, **kwargs):
        r'''Draw my texture.
        '''
        attrs = extend(self, template, **kwargs)
        if self.as_sprite:
            self.sprite.save_pos(attrs.x_left, attrs.y_upper)
        texture = self.texture.texture.texture
        x = Si(attrs.x_pos, texture.width)
        y = Si(attrs.y_pos, texture.height)
        draw_texture(texture, x, y, WHITE)
"""


if __name__ == "__main__":
    import doctest
    doctest.testmod()
