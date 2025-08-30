# methods.py

from string import Template


__all__ = "init_method specialize_fn draw_method clear_method".split()


class method:
    first_auto_params = {}
    widget_attrs = 'layout appearance computed_init computed_draw output'.split()
    self_arg = "self"

    def __init__(self, widget, trace=False):
        self.trace = trace
        self.widget = widget
        for name in self.widget_attrs:
            setattr(self, name, getattr(widget, name))

        self.params = []  # list of (pname, iname, sname, exp|None), exp is None if in param list
        self.args = []
        for pname, iname, sname, exp in self.get_params():  # list of (pname, iname, sname, exp)
            if not isinstance(exp, str) or exp[0].isupper() or exp[0] == '"' or exp[0] == "'":
                arg = f"{pname}={exp}"
                self.params.append((pname, iname, sname, None))
            else:
                arg = f"{pname}=None"
                self.params.append((pname, iname, sname, exp))
            self.args.append(arg)

        if self.trace:
            print(f"{self.__class__.__name__}.__init__({self.widget.name}): get_params():")
            for pname, iname, sname, exp in self.get_params():
                print(f"  {pname=}, {iname=}, {sname=}, {exp=}")

    def gen_method(self):
        self.start()           # prints def __init__(...):
        self.output.indent()
        self.body()            # assignments
        self.end()             # final if trace: and include, etc init
        self.output.deindent()
        self.output.print()

    def start(self):
        self.output.print_args(f"def {self.method_name}({self.self_arg}", self.args,
                               first_comma=bool(self.self_arg))

    def get_first_auto_params(self):
        r'''Returns a new list of (pname, iname, sname, exp)
        '''
        return [(pname, pname, 'self.' + pname, exp) for pname, exp in self.first_auto_params]

    def get_final_auto_params(self):
        r'''Returns a new list of (pname, iname, sname, exp)
        '''
        return []

    def get_params(self):
        r'''Returns list of (pname, iname, sname, exp) for each param
        '''
        first_auto_params = self.get_first_auto_params()
        final_auto_params = self.get_final_auto_params()
        params = first_auto_params
        for vars in self.param_vars:  # e.g., 'layout', 'appearance'
            params.extend(self.as_params(getattr(self, vars)))
        params.extend(final_auto_params)
        return params

    def body(self):
        # e.a.b -> e__a.b
        for pname, _, sname, exp in self.params:
            self.output_copy(pname, sname, exp)
        # e.a.b -> e__a.b
        # s.a.b -> x.a.b
        if self.trace:
            print(f"{self.__class__.__name__}.body({self.widget.name})")
        self.gen_computed()
        # end takes care of if trace and includes

class init_method(method):
    method_name = '__init__'
    first_auto_params = ()
    final_auto_params = (('trace', False),)
    param_vars = 'layout', 'appearance'

    def get_first_auto_params(self):
        r'''Returns a new list of (pname, iname, sname, exp).
        '''
        params = [('name', f'"a {self.widget.name}"')]
        params.extend(self.first_auto_params)
        return [(pname, pname, 'self.' + pname, exp) for pname, exp in params]

    def get_final_auto_params(self):
        r'''Returns a new list of (pname, iname, sname, exp).
        '''
        params = []
        if hasattr(self.widget, 'placeholders') and self.widget.placeholders:
            params.append(('placeholders', None))
        params.extend(self.final_auto_params)
        return [(pname, pname, 'self.' + pname, exp) for pname, exp in params]

    def as_params(self, vars):
        r'''Returns a list of (pname, iname, sname, default) pairs ready for get_params.
        '''
        return vars.map_pitems(lambda pname, var: (pname, var.iname, var.sname, var.exp))

    def output_copy(self, pname, sname, exp):
        if pname == 'placeholders':
            self.output.print(f"{sname} = {pname}")
            for name in self.widget.placeholders:
                template = Template("""
                   widgets = []
                   for info in self.placeholders["$name"]:
                       name, widget = info.copy().popitem()
                       setattr(self, name, widget)
                       widgets.append(widget)
                   ${name}__width = $width_agg_fn(widget.width for widget in widgets)
                   ${name}__height = $height_agg_fn(widget.height for widget in widgets)
                """)
                self.output.print_block(
                  template.substitute(name=name,
                                      width_agg_fn=self.widget.width_agg_fn,
                                      height_agg_fn=self.widget.height_agg_fn))
        elif exp is None:
            self.output.print(f"{sname} = {pname}")
        else:
            template = Template("""
               if $pname is None:
                   $sname = $exp
               else:
                   $sname = $pname
            """)
            self.output.print_block(template.substitute(pname=pname, sname=sname, exp=exp))

    def gen_computed(self):
        needed = set(self.widget.init_needed())

        # force generation of all computed names so that draw has access to them too.
        needed.update(self.computed_init.gen_inames())

        self.computed_init.gen_vars(needed, self, self.trace)

    def end(self):
        self.widget.init_calls()
        self.output.print("if trace:")
        self.output.indent()
        args = ', '.join(f'{{{sname}=}}' for sname in self.appearance.gen_snames())
        self.output.print(f'print(f"{self.widget.name}({{self.name}}).__init__: {args}")')
        self.output.deindent()
        if 'init' in self.widget.include:
            self.output.print_block(self.widget.include.pop('init'))

class specialize_fn(init_method):
    widget_attrs = 'layout appearance computed_init output'.split()
    self_arg = ""

    def __init__(self, widget, trace=False):
        super().__init__(widget, trace)
        self.method_name = self.widget.name

    def get_final_auto_params(self):
        r'''Returns a new list of (pname, iname, sname, exp).
        '''
        params = self.final_auto_params
        return [(pname, pname, 'self.' + pname, exp) for pname, exp in params]

    def body(self):
        for pname, iname, sname, exp in self.params:
            if exp is not None:
                template = Template("""
                    if $pname is None:
                        $pname = $exp
                """)
                self.output.print_block(template.substitute(pname=pname, exp=exp))
        if self.trace:
            print(f"{self.__class__.__name__}.body({self.widget.name})")
        self.gen_computed()

    def end(self):
        self.widget.init_calls()
        self.output.print("if trace:")
        self.output.indent()
        args = ', '.join(f'{{{sname}=}}' for sname in self.appearance.gen_snames())
        self.output.print(f'print(f"{self.widget.name}({{name}}).__init__: {args}")')
        self.output.deindent()
        if 'init' in self.widget.include:
            self.output.print_block(self.widget.include.pop('init'))
        self.output.print("return ans")

class draw_method(method):
    method_name = 'draw'
    first_auto_params = (('x_pos', None), ('y_pos', None))
    param_vars = 'appearance',

    def as_params(self, vars):
        r'''Returns a list of (pname, iname, sname, None) pairs ready for get_params.
        '''
        return vars.map_pitems(lambda pname, var: (pname, var.iname, var.sname, None))

    def gen_computed(self):
        self.computed_draw.gen_vars(self.widget.draw_needed(), self, self.trace)

    def output_copy(self, pname, sname, exp):  # exp ignored
        template = Template("""
            if $pname is not None:
                $sname = $pname
        """)
        self.output.print_block(template.substitute(pname=pname, sname=sname))

    def end(self):
        self.output.print("if self.trace:")
        self.output.indent()
        args = ', '.join(f'{{{sname}=}}' for sname in self.appearance.gen_snames())
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

    def gen_computed(self):
        pass

    def body(self):
        pass

    def end(self):
        added = self.widget.clear_calls()
        if 'clear' in self.widget.include:
            self.output.print_block(self.widget.include.pop('clear'))
            added = True
        if not added:
            self.output.print("pass")

