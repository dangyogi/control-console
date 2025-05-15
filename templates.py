# templates.py

r'''Various Template subclasses:

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

import exp
import texture
import shapes
import context


icon_base = context.area()

class Icon(context.Template):
    r'''Creates its own render texture and draws its components on it during init().

    Then just draws its texture in draw().

    This is sprite enabled.
    '''
    base = icon_base

    def init(self, template=None, **kwargs):
        super().init(template, as_sprite=False)          # sets width and height
        attrs = Context(self, template, **kwargs)        # I'm only the template for my components
        self.texture = texture.Texture(attrs.width, attrs.height)
        with self.texture.draw_on_texture():
            super().draw(template, **kwargs)
        if attrs.as_sprite:
            self.sprite = sprite.Sprite(self.width, self.height, attrs.dynamic_capture)

    def draw(self, template=None, **kwargs):
        r'''Draw my texture.
        '''
        attrs = Context(self, template, **kwargs)
        if self.as_sprite:
            self.sprite.save_pos(attrs.x_left, attrs.y_upper)
        texture = self.texture.texture.texture
        x = Si(attrs.x_pos, texture.width)
        y = Si(attrs.y_pos, texture.height)
        draw_texture(texture, x, y, WHITE)



if __name__ == "__main__":
    import doctest
    doctest.testmod()
