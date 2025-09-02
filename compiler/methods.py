# methods.py

from string import Template

from variable import *
from tsort import tsort


__all__ = "init_method specialize_fn draw_method clear_method".split()


class method:
    first_auto_params = ()
    widget_attrs = 'layout appearance computed_init computed_draw output'.split()
    self_arg = "self"

    def __init__(self, widget, trace):
        self.trace = trace
        self.widget = widget
        for name in self.widget_attrs:
            setattr(self, name, getattr(widget, name))
        if "method__init__dump" in self.trace:
            print(f"{self.__class__.__name__}.__init__({self.widget.name}): gen_params():")
            for variable in self.gen_params():
                print(f"  {variable.pname=}, {variable.ename=}, {variable.sname=}, {variable.exp=}")

    def gen_method(self):
        self.start()           # prints def __init__(...):
        self.output.indent()
        self.body()            # assignments
        self.end()             # final if trace: and include, etc init
        self.output.deindent()
        self.output.print()

    def start(self):
        self.output.print_head(f"def {self.method_name}({self.self_arg}",
                               first_comma=bool(self.self_arg))
        for variable in self.gen_params():
            self.output.print_arg(variable.as_param())
        self.output.print_tail('):')

    def body(self):
        # e.a.b -> e__a.b
        for variable in self.gen_params():
            variable.load(self)
        # e.a.b -> e__a.b
        # s.a.b -> x.a.b
        if "body" in self.trace:
            print(f"{self.__class__.__name__}.body({self.widget.name})")
        self.gen_computed()
        # end takes care of if trace and includes

    def gen_params(self):
        r'''Generates a variable for each param, some are pseudo_variables.
        '''
        yield from self.get_first_auto_params()
        for vars in self.param_vars:  # e.g., 'layout', 'appearance'
            yield from self.as_params(getattr(self, vars))
        yield from self.get_final_auto_params()

    def get_first_auto_params(self):
        r'''Returns a new list of pseudo_variables
        '''
        return [pseudo_variable(pname, pname, 'self.' + pname, exp)
                for pname, exp in self.first_auto_params]

    def get_final_auto_params(self):
        r'''Returns an empty list (of variables)
        '''
        return []

    def available_variables(self):
        for vars in self.available_vars:
            yield from getattr(self, vars).gen_variables()

class init_method(method):
    method_name = '__init__'
    first_auto_params = ()
    final_auto_params = (('trace', False),)
    param_vars = 'layout', 'appearance'
    available_vars = 'layout', 'appearance', 'computed_init'

    def get_first_auto_params(self):
        r'''Returns a new list of pseudo_variables
        '''
        params = [('name', f'"a {self.widget.name}"')]
        params.extend(self.first_auto_params)
        return [pseudo_variable(pname, pname, 'self.' + pname, exp) for pname, exp in params]

    def get_final_auto_params(self):
        r'''Returns a new list of pseudo_variables
        '''
        params = []
        if hasattr(self.widget, 'placeholders') and self.widget.placeholders:
            params.append(('placeholders', None))
        params.extend(self.final_auto_params)
        return [pseudo_variable(pname, pname, 'self.' + pname, exp) for pname, exp in params]

    def as_params(self, vars):
        r'''Generates variables from vars

        Called from gen_params.
        '''
        return vars.gen_variables()

    def load_create_widget(self, variable):
        self.output.print_head(f"{variable.sname} = {variable.widget_name}(", first_comma=False)
        for arg in variable.args:
            self.output.print_arg(arg)
        self.output.print_tail(')')

    def load_param(self, variable):
        pname = variable.pname
        self.output.print(f"{variable.sname} = {pname}")
        if pname == 'placeholders':  # placeholders is {name: [name, widget]}
            template = Template("""
               widgets = []
               for info in self.placeholders["$name"]:
                   name, widget = info.copy().popitem()
                   setattr(self, name, widget)
                   widgets.append(widget)
               ${name}__width = $width_agg_fn(widget.width for widget in widgets)
               ${name}__height = $height_agg_fn(widget.height for widget in widgets)
            """)
            for name in self.widget.placeholders:
                self.output.print_block(
                  template.substitute(name=name,
                                      width_agg_fn=self.widget.width_agg_fn,
                                      height_agg_fn=self.widget.height_agg_fn))

    def load_computed(self, variable):
        self.output.print(f"{variable.sname} = {variable.exp}")

    def load_computed_param(self, variable):
        template = Template("""
           if $pname is not None:
               $sname = $pname
           else:
               $sname = $exp
        """)
        self.output.print_block(template.substitute(pname=variable.pname,
                                                    sname=variable.sname,
                                                    exp=variable.exp))

    def gen_computed(self):
        self.computed_init.init(self)

        # force generation of all computed names so that draw has access to them too.
        needed = set(self.widget.computed_init.gen_names())

        for variable in tsort(self.computed_init, needed, self.trace):
            variable.load(self)

    def end(self):
        self.widget.init_calls()
        self.output.print("if trace:")
        self.output.indent()
        args = ', '.join(f'{{{ename}=}}' for ename in self.appearance.gen_names())
        self.output.print(f'print(f"{self.widget.name}({{self.name}}).__init__: {args}")')
        self.output.deindent()
        if 'init' in self.widget.include:
            self.output.print_block(self.widget.include.pop('init'))

class specialize_fn(init_method):
    widget_attrs = 'layout appearance computed_init output'.split()
    self_arg = ""

    def __init__(self, widget, trace):
        super().__init__(widget, trace)
        self.method_name = self.widget.name

    def get_final_auto_params(self):
        r'''Returns a new list of pseudo_variables
        '''
        params = self.final_auto_params
        return [pseudo_variable(pname, pname, pname, exp) for pname, exp in params]

    def load_param(self, variable):
        self.output.print(f"specialize_fn.load_param({variable.pname=}) FYI: called")
        ''' FIX
        if exp is not None:
            template = Template("""
                if $pname is None:
                    $pname = $exp
            """)
            self.output.print_block(template.substitute(pname=pname, exp=exp))
        '''

    def end(self):
        super().end()
        self.output.print("return ans")

class draw_method(method):
    method_name = 'draw'
    first_auto_params = (('x_pos', None), ('y_pos', None))
    param_vars = 'appearance',
    available_vars = 'appearance', 'computed_draw'

    def as_params(self, vars):
        r'''Returns a list of pseudo_variables copied from vars with exp set to None.

        Called from gen_params.
        '''
        return [pseudo_variable(var.pname, var.ename, var.sname) for var in vars.gen_variables()]

    def gen_computed(self):
        self.computed_draw.init(self)
        for variable in tsort(self.computed_draw, self.widget.draw_needed(), self.trace):
            variable.load(self)

    def load_param(self, variable):  # exp ignored
        template = Template("""
            if $pname is not None:
                $sname = $pname
        """)
        self.output.print_block(template.substitute(pname=variable.pname, sname=variable.sname))

    def end(self):
        self.output.print("if self.trace:")
        self.output.indent()
        args = ', '.join(f'{{{ename}=}}' for ename in self.appearance.gen_names())
        self.output.print(f'print(f"{self.widget.name}({{self.name}}).draw: {args}")')
        self.output.deindent()
        if 'draw_before' in self.widget.include:
            self.output.print_block(self.widget.include.pop('draw_before'))
        self.widget.output_draw_calls(self)
        if 'draw_end' in self.widget.include:
            self.output.print_block(self.widget.include.pop('draw_end'))

class clear_method(method):
    method_name = 'clear'
    param_vars = ()
    available_vars = ()

    def body(self):
        pass

    def end(self):
        added = self.widget.clear_calls()
        if 'clear' in self.widget.include:
            self.output.print_block(self.widget.include.pop('clear'))
            added = True
        if not added:
            self.output.print("pass")

