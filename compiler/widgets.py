# widgets.py

from string import Template
from itertools import chain

from methods import *
from vars import *
from variable import *


__all__ = "raylib_call stacked column row specializes widget_stub Widget_types Widgets".split()


Widgets = {}

class widget:
    skip = False
    element_names = ()     # element names, excluding placeholders
    element_widgets = ()   # widget names, excluding placeholders, used by translate_exp
    computed_vars = ((computed_init, False), (computed_draw, False))

    def __init__(self, name, spec, output):
        self.spec = spec
        self.trace_init = self.spec.pop('trace_init', False)
        self.trace_draw = self.spec.pop('trace_draw', False)
        self.name = name
        self.output = output
        self.include = self.spec.pop('include', {})

        # create helpers
        for section, trace in (shortcuts, False), (layout, False), (appearance, False):
            name = section.name
            setattr(self, name, section(self.spec.pop(name, {}), self, trace))
        computed = self.spec.pop('computed', {})
        for section, trace in self.computed_vars:
            name = section.name
            subname = name[9:]
            #print(f"{self.__class__.__name__}({self.name}).__init__: {name=}, {subname=}")
            setattr(self, name, section(computed.pop(subname, {}), self, trace))
        if computed:
            print("unknown keys in 'computed' spec for", self.name, tuple(self.computed.keys()))

        Widgets[self.name] = self

        # Called before computed_X helpers are fully initialized
        # creates methods, may override assignment to Widgets and add_compute to computed_init/draw...
        self.init()

        for section, _ in self.computed_vars:
            section_name = section.name
            getattr(self, section_name).init2()

        # after all helpers are fully initialized
        self.init2()

        if self.trace_init:
            print(f"widget({self.name}).__init__: {self.init_params()=}")
        if self.trace_draw:
            print(f"widget({self.name}).__init__: {self.draw_params()=}")
        if self.spec:
            print("unknown keys in spec for", self.name, tuple(self.spec.keys()))

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def init(self):
        self.init_method = init_method(self, self.trace_init)
        self.draw_method = draw_method(self, self.trace_draw)
        self.clear_method = clear_method(self)

    def init2(self):
        pass

    def init_params(self):
        r'''Returns {pname: default_exp}
        '''
        return {pname: exp for pname, _, _, exp in self.init_method.get_params()}

    def init_available(self):
        r'''Returns a new {iname: sname} of available inames within the __init__ method.

        Can only be done after init2 call is done.
        '''
        ans = {iname: sname for pname, iname, sname, exp in self.init_method.get_params()}
        def add_key(iname, vars):
            ans[iname] = vars.sname
        self.computed_init.map_iitems(add_key)
        return ans

    def init_available_inames(self):
        r'''Returns a new set(iname) of available inames within the __init__ method.

        This can be done before the init2 calls are made.
        '''
        ans = set((iname for pname, iname, sname, exp in self.init_method.get_params()))
        ans.update(self.computed_init.gen_inames())
        return ans

    def draw_params(self):
        r'''Returns [pname]

        These always default to None.
        '''
        return [pname for pname, _, _, _ in self.draw_method.get_params()]

    def draw_available(self):
        r'''Returns a new {iname: sname} of available inames within the draw method.

        This does not include computed_draw info.
        '''
        return {iname: sname for iname, sname in self.init_available().items()
                             if sname.startswith("self.")}

    def draw_computable(self):
        r'''Returns a new {iname: sname} of computable inames within the draw method.

        This does not include draw_available info.

        If you need any of these, you must add the iname to needs.
        '''
        ans = {}
        def add_key(iname, vars):
            ans[iname] = vars.sname
        self.computed_draw.map_iitems(add_key)
        return ans

    def generate_widget(self):
        self.start_class()

        self.init_method.gen_method()

        template = Template("""
            def __repr__(self):
                return f"<$name {self.name} @ {self.id()}>"

        """)
        self.output.print_block(template.substitute(name=self.name))

        self.draw_method.gen_method()
        self.clear_method.gen_method()

        self.end_class()
        if self.include:
            print("unknown keys in 'include' spec for", self.name, tuple(self.include.keys()))

    def start_class(self):
        self.output.print(f"class {self.name}:")
        self.output.indent()

    def end_class(self):
        self.output.deindent()

    def init_calls(self):
        pass

    def init_needed(self):
        return ()

    def draw_needed(self):
        return ()

    def clear_calls(self):
        r'''Return True if something was added.
        '''
        return False

class raylib_call(widget):
    def init(self):
        super().init()
        raylib_call = self.spec.pop('raylib_call')
        self.raylib_fn = raylib_call['name']    # something defined in pyray (raylib) library
        self.raylib_args = raylib_call['args']  # these are inames

    def output_draw_calls(self, method):
        self.output.print_head(f"{self.raylib_fn}(", first_comma=False)
        for name in self.raylib_args:
            if name in self.computed_draw:
                self.output.print_arg(name)
            else:
                self.output.print_arg(f"self.{name}")
        self.output.print_tail(")")

    def draw_needed(self):
        return frozenset(self.raylib_args).intersection(self.computed_draw.gen_inames())

class composite(widget):
    e_x_pos = "getattr(x_pos, self.x_align)(self.width)"
    e_y_pos = "getattr(y_pos, self.y_align)(self.height)"

    def __init__(self, name, spec, output):
        #print(f"{name}.__init__: {elements=}")
        cls_name = self.__class__.__name__
        cls_section = spec.pop(cls_name)
        self.raw_elements = cls_section.pop('elements')
        if cls_section:
            print(f"unknown keys in {cls_name} section for {name}, "
                  f"{tuple(cls_section.keys())}")
        super().__init__(name, spec, output)    # calls self.init()

    def init(self):
        r'''Called after everything else is initialized in widget.
        '''
        super().init()
        self.elements = []
        self.placeholders = []
        self.element_names = set()
        self.element_widgets = set()

        # add inames to computed_init before calling init_available_X
        second_pass = []
        for elem in self.raw_elements:
            assert len(elem) == 1, f"expected element dict with one key, got {elem=}"
            name, widget_name = elem.copy().popitem()
            if widget_name == "placeholder":
                self.placeholders.append(name)
                self.elements.append((name, None))
            else:
                widget = Widgets[widget_name]
                self.element_names.add(name)
                self.element_widgets.add(widget_name)
                self.elements.append((name, widget))
                second_pass.append((name, widget))
                self.computed_init.add_compute(name, None)

        computed_draw_inames = frozenset(self.computed_draw.gen_inames())
        self.needed_draw_names = []
        for name, widget in second_pass:
            self.needed_draw_names.extend(
              computed_draw_inames.intersection(
                (f"{name}__{pname}" for pname in widget.draw_params())))
            init_available = self.init_available_inames()  # set(iname)
            init_params = [f"{name}__{pname}" for pname in widget.init_params().keys()]
            params_to_pass = init_available.intersection(init_params)
            args_to_pass = [f"{my_iname[len(name) + 2:]}={my_iname}" 
                            for my_iname in params_to_pass]
            if self.trace_init:
                print(f"{self.name}.init:")
                print(f"  {init_available=}")
                print(f"  {init_params=}")
                print(f"  {params_to_pass=}")
                print(f"  {args_to_pass=}")
            name_pname = f"{name}__name"
            if name_pname not in params_to_pass:
                args_to_pass.insert(0, f'name="{name}"')
                if self.trace_init:
                    print(f"added name {name=}, {name_pname=}, {args_to_pass[0]=}")
            exp = f"{widget_name}({', '.join(args_to_pass)})"
            if self.trace_init:
                print(f"add_compute({name=}, {exp=}")
            self.computed_init.add_compute(name, exp)
        self.sub_init()

    def sub_init(self):
        pass

    def init_calls(self):
        self.output.print_head(f"self.width = {self.width_agg_fn}(", first_comma=False)
        for element in self.element_names:
            self.output.print_arg(f"self.{element}.width")
        for placeholder in self.placeholders:
            self.output.print_arg(f"self.{placeholder}__width")
        self.output.print_tail(')')
        self.output.print_head(f"self.height = {self.height_agg_fn}(", first_comma=False)
        for element in self.element_names:
            self.output.print_arg(f"self.{element}.height")
        for placeholder in self.placeholders:
            self.output.print_arg(f"self.{placeholder}__height")
        self.output.print_tail(')')

    def draw_needed(self):
        return self.needed_draw_names

    def output_draw_calls(self, method):
        self.output.print(f"e_x_pos = {self.e_x_pos}")
        self.output.print(f"e_y_pos = {self.e_y_pos}")
        draw_available = self.draw_available()
        for name, widget in self.elements:
            if widget is not None:
                self.output.print_head(f"self.{name}.draw(", first_comma=False)
                self.output.print_arg('x_pos=e_x_pos')
                self.output.print_arg('y_pos=e_y_pos')
                for pname in widget.draw_params():
                    my_iname = f"{name}__{pname}"
                    if my_iname in draw_available:
                        self.output.print_arg(f"{pname}={draw_available[my_iname]}")
                    elif my_iname in self.needed_draw_names:
                        self.output.print_arg(f"{pname}=self.{my_iname}")
                self.output.print_tail(')')
                self.inc_draw_pos("self." + name)
            else:
                template = Template("""
                   for info in self.placeholders["$name"]:
                       name, _widget = info.copy().popitem()
                       widget = getattr(self, name)
                       widget.draw(x_pos=e_x_pos, y_pos=e_y_pos)
                """)
                self.output.print_block(template.substitute(name=name))
                self.output.indent()
                self.inc_draw_pos("widget")
                self.output.deindent()

    def inc_draw_pos(self, sname):
        pass

    def clear_calls(self):
        r'''Return True if something was added.
        '''
        added = False
        for name, widget in self.elements:
            if widget is not None:
                self.output.print(f"self.{name}.clear()")
            else:
                template = Template("""
                   for info in self.placeholders["$name"]:
                       name, _widget = info.copy().popitem()
                       widget = getattr(self, name)
                       widget.clear()
                """)
                self.output.print_block(template.substitute(name=name))
            added = True
        return added

class stacked(composite):
    width_agg_fn = "max"
    height_agg_fn = "max"

    def sub_init(self):
        self.layout.add_var(param_var(self, 'x_align', '"C"'))
        self.layout.add_var(param_var(self, 'y_align', '"C"'))

class column(composite):
    e_y_pos = "y_pos.S(self.height)"
    width_agg_fn = "max"
    height_agg_fn = "sum"

    def sub_init(self):
        self.layout.add_var(param_var(self, 'x_align', '"C"'))

    def inc_draw_pos(self, sname):
        self.output.print(f"e_y_pos += {sname}.height")

class row(composite):
    e_x_pos = "x_pos.S(self.width)"
    width_agg_fn = "sum"
    height_agg_fn = "max"

    def sub_init(self):
        self.layout.add_var(param_var(self, 'y_align', '"C"'))

    def inc_draw_pos(self, sname):
        self.output.print(f"e_x_pos += {sname}.width")

class specializes(widget):
    computed_vars = ((computed_specialize, True),)
    #skip = True

    def init(self):
        self.base_widget = self.spec.pop("specializes")
        self.placeholders = self.spec.pop("placeholders", None)
        self.init_method = specialize_fn(self, self.trace_init)
        if self.placeholders is not None:
            second_pass = []
            for placeholder_name, elements in self.placeholders.items():
                for element in elements:
                    name, widget = element.copy().popitem()
                    second_pass.append((name, widget))
                    self.computed_init.add_compute(name, None) # add inames before calling widget_exp
            for name, widget in second_pass:
                head, args, tail = self.widget_exp(widget, f'{name}__', f'name="{name}"')
                self.computed_init.add_compute(name, head + ', '.join(args) + tail)

    def generate_widget(self):
        self.init_method.gen_method()
        if self.include:
            print("unknown keys in 'include' spec for", self.name, tuple(self.include.keys()))

    def init_calls(self):
        widget_args = []
        if self.placeholders is not None:
            #placeholders_arg = dict(
            #    body=[dict(name: element)],
            #    )
            self.output.print_head("placeholders_arg = dict(", first_comma=False)
            for placeholder_name, elements in self.placeholders.items():
                elements_arg = []
                for element in elements:
                    name, widget = element.copy().popitem()
                    elements_arg.append(f"dict({name}={name})")
                self.output.print_arg(f"{placeholder_name}=[{', '.join(elements_arg)}]")
            self.output.print_tail(')')
            widget_args.append("placeholders=placeholders_arg")
        head, args, tail = self.widget_exp(self.base_widget, "", *widget_args)
        self.output.print_args("ans = " + head, args, tail=tail, first_comma=False)

    def widget_exp(self, widget_name, prefix, *args):
        widget = Widgets[widget_name]
        head = f"{widget_name}("
        args = list(args)
        available_names = self.init_available_inames()  # set(inames)
        init_params = [f'{prefix}{name}' for name in widget.init_params().keys()]  # pnames
        args.extend([f'{name[len(prefix):]}={self.shortcuts.desubstitute(name)}'
                     for name in available_names.intersection(init_params)])
        if self.trace_init:
            print(f"{self.name}.widget_exp({widget_name=}):")
            print(f"  {available_names=}")
            print(f"  {init_params=}")
            print(f"  {args=}")
        return head, args, ')'

class widget_stub:
    def __init__(self, name, layout=(), appearance=()):
        self.name = name
        self.layout = dict(((name, None) for name in layout))
        self.appearance = dict(((name, None) for name in appearance))

    def init_params(self):
        r'''Returns {pname: default_exp}
        '''
        return {name: exp for name, exp in chain(self.layout.items(), self.appearance.items())}

    def draw_params(self):
        return []

Widget_types = (raylib_call, stacked, column, row, specializes)
