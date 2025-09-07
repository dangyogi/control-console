# vars.py

from tsort import *
from variable import *


__all__ = "layout appearance computed_init computed_specialize computed_draw " \
          "shortcuts raylib_args".split()


class base_vars:
    use_ename = True  # use ename for sname base, else yaml name
    use_self = True
    added = ()

    def __init__(self, widget, trace):
        self.trace = trace
        self.widget = widget
        self.output = self.widget.output  # FIX: still needed?
        self.enames = {}

    def __contains__(self, ename):
        return ename in self.enames

    def __getitem__(self, ename):
        return self.enames[ename]

    def dump(self):
        print(f"{self.__class__.__name__}.dump:")
        for ename, variable in self.enames.items():
            print(f"  {ename=}: {variable=}")

    def gen_names(self):
        return self.enames.keys()

    def gen_variables(self):
        return self.enames.values()

    def add_var(self, name, exp):
        r'''Ignores request if name already in self.enames.
        '''
        self.index_var(self.variable_class(self, name, exp))

    def index_var(self, var):
        r'''Ignores request if var.ename already in self.enames.
        '''
        if var.ename not in self.enames:
            self.enames[var.ename] = var

class vars(base_vars):
    r'''This encapsulates {name: exp} dicts in the yaml file.

    The vars parameter to __init__ is the raw yaml data.  It has not been processed or converted.

    Created by widget.__init__.
    '''
    def __init__(self, vars, widget, trace):
        super().__init__(widget, trace)
        all_vars = dict(self.added)  # {name: exp}
        all_vars.update(vars)        # overrides added
        for name, exp in all_vars.items():
            self.add_var(name, exp)

class params(vars):
    variable_class = param_var

class layout(params):
    name = "layout"

class appearance(params):
    name = "appearance"

class computed(base_vars):
    variable_class = computed_var

    def init(self, method):
        for variable in self.gen_variables():
            variable.init(method)

class computed_init(computed, vars):
    name = "computed_init"

    def add_create_widget(self, child_name, widget_name, *args):
        r'''Ignores request if child_name already in self.enames.
        '''
        self.index_var(computed_create_widget(self, child_name, widget_name, args))

class computed_specialize(computed_init):
    use_ename = False
    use_self = False

class computed_draw(computed, vars):
    name = "computed_draw"
    added = (('draw_height', 'height'),
             ('draw_width', 'width'),

             ('x_left', 'x_pos.S(draw_width)'),
             ('x_center', 'x_pos.C(draw_width)'),
             ('x_right', 'x_pos.E(draw_width)'),
             ('y_top', 'y_pos.S(draw_height)'),
             ('y_middle', 'y_pos.C(draw_height)'),
             ('y_bottom', 'y_pos.E(draw_height)'),
            )
    use_self = False

class shortcuts:
    r'''Only used to translate shortcut pnames to expanded inames.

    Used by params.init, computed_var.translate_name and specializes.widget_exp
    '''
    name = "shortcuts"

    def __init__(self, vars, widget, trace):
        self.widget = widget
        self.trace = trace

        # {name: sname}
        self.names = vars

        # {sname: name}
        self.snames = {sname: name for name, sname in self.names.items()}

    def dump(self):
        print(f"shortcuts.dump:")
        for name, sname in self.names.items():
            print(f"  {name=}: {sname=}")

    def substitute(self, name):
        return self.names.get(name, name)

    def desubstitute(self, sname):
        return self.snames.get(sname, sname)

class raylib_args(base_vars):
    use_ename = False
    variable_class = raylib_arg

    def __init__(self, args, widget, trace):
        super().__init__(widget, trace)
        self.needs = set()
        for i, exp in enumerate(args, 1):
            self.add_var(f"_p{i}", exp)

    def init(self, method, needs):
        for variable in self.gen_variables():
            variable.init(method, needs)

