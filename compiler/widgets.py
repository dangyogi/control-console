# widgets.py

from string import Template
from itertools import chain

from methods import *
from vars import *


__all__ = "raylib_call stacked column row panel specializes " \
          "widget_stub Widget_types Widgets".split()


Widgets = {}

class widget:
    r'''A widget only has two external steps:

        1. call to __init__
        2. call to it's generate_widget

    These are both done before compiling the next widget in the yaml file.
    '''
    Widgets = Widgets      # so anybody with any widget can find this...
    skip = False
    element_names = ()     # element names, excluding placeholders
    element_widgets = ()   # widget names, excluding placeholders, used by translate_exp
    vars = (shortcuts, layout, appearance)
    computed_vars = (computed_init, computed_draw)
    methods = (init_method, draw_method, clear_method)
    use_ename = True
    use_self = True

    def __init__(self, name, spec, output, trace):
        r'''
        trace is bool set by compiler.compile based on command line --trace widgets.
        If false, this turns off the widget's trace: key in the yaml file by setting self.trace = ().
        If True, self.trace is set to the trace: key in the yaml file.
        Which is a list of names to trace.
        '''
        self.name = name
        self.spec = spec
        self.output = output

        # pop this regardless of trace...
        self.trace = self.spec.pop('trace', ())

        if not trace:
            self.trace = ()

        self.include = self.spec.pop('include', {})

        # create helpers
        if shortcuts not in self.vars:
            self.shortcuts = shortcuts({}, self, self.trace)
        for section in self.vars:
            name = section.name
            setattr(self, name, section(self.spec.pop(name, {}), self, self.trace))
        computed = self.spec.pop('computed', {})
        for section in self.computed_vars:
            name = section.name
            subname = name[9:]
            #print(f"{self.__class__.__name__}({self.name}).__init__: {name=}, {subname=}")
            setattr(self, name, section(computed.pop(subname, {}), self, self.trace))
        if computed:
            print("unknown keys in 'computed' spec for", self.name, tuple(self.computed.keys()))

        for method in self.methods:
            name = method.__name__
            setattr(self, name, method(self, self.trace))

        Widgets[self.name] = self

        # may add to computed_init/draw...
        self.init()

        if "show_shortcuts" in self.trace:
            self.shortcuts.dump()
        if "show_layout" in self.trace:
            self.layout.dump()
        if "show_appearance" in self.trace:
            self.appearance.dump()
        if "show_computed_init" in self.trace:
            self.computed_init.dump()
        if "show_computed_draw" in self.trace:
            self.computed_draw.dump()
        if "show_init_params" in self.trace:
            print(f"widget({self.name}).__init__: {self.init_params()=}")
        if "show_init_available" in self.trace:
            print(f"widget({self.name}).__init__: {self.init_available()=}")
        if "show_draw_params" in self.trace:
            print(f"widget({self.name}).__init__: {self.draw_params()=}")
        if "show_draw_available" in self.trace:
            print(f"widget({self.name}).__init__: {self.draw_available()=}")
        if "show_draw_computable" in self.trace:
            print(f"widget({self.name}).__init__: {self.draw_computable()=}")
        if self.spec:
            print("unknown keys in spec for", self.name, tuple(self.spec.keys()))

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def init(self):
        pass

    def create_widget_args(self, method, widget_name, prefix, *args):
        r'''Returns a list of arguments to pass to widget_name ctor, and a set of needs
        '''
        # we want these args to be overridden if there are available args of the same name.
        args_dict = {}
        for arg in args:
            name, exp = arg.split('=', 1)
            args_dict[name] = exp

        init_params = frozenset(
                        pname
                        for pname, default in Widgets[widget_name].init_params().items())
        avail_params = {variable.ename[len(prefix):]: variable            # {pname: variable}
                        for variable in method.available_variables()
                        if variable.ename.startswith(prefix)
                       }
        needs = set()
        for pname in init_params.intersection(avail_params.keys()):
            avail_param = avail_params[pname]
            if "create_widget_args" in self.trace:
                print(f"  {pname=}: {avail_param=}, {avail_param.sname=}, {avail_param.is_computed=}")
            args_dict[pname] = avail_param.sname
            if avail_param.is_computed:
                needs.add(avail_param.ename)
        if "create_widget_args" in self.trace:
            print(f"widget({self.name}).create_widget_args(method={method.method_name}, "
                  f"{widget_name=}, {prefix=}, {args=}):")
            print(f"  {init_params=}")
            print(f"  {avail_params=}")
            print(f"  {args_dict=}")
            print(f"  {needs=}")
        return [f"{name}={exp}" for name, exp in args_dict.items()], needs

    def init_params(self):
        r'''Returns {pname: default_exp}
        '''
        return {variable.pname: variable.exp for variable in self.init_method.gen_params()}

    def init_available(self):
        r'''Returns a new {ename: sname} of available enames within the __init__ method.
        '''
        ans = {variable.ename: variable.sname for variable in self.init_method.gen_params()}
        for variable in self.computed_init.gen_variables():
            ans[variable.ename] = variable.sname
        return ans

    def init_available_enames(self):
        r'''Returns a new set(ename) of available names within the __init__ method.
        '''
        ans = set((variable.ename for variable in self.init_method.gen_params()))
        ans.update(self.computed_init.gen_names())
        return ans

    def draw_params(self):
        r'''Returns [pname]

        These always default to None.
        '''
        return [variable.pname for variable in self.draw_method.gen_params()]

    def draw_available(self):
        r'''Returns a new {ename: sname} of available inames within the draw method.

        This does not include computed_draw info.
        '''
        ans = {variable.ename: variable.sname
               for variable in self.draw_method.get_first_auto_params()}
        ans.update((ename, sname) for ename, sname in self.init_available().items()
                                  if sname.startswith("self."))
        ans.update((variable.ename, variable.sname)
                   for variable in self.draw_method.get_final_auto_params())
        return ans

    def draw_computable(self):
        r'''Returns a new {ename: sname} of computable enames within the draw method.

        This does not include draw_available info.

        If you need any of these, you must add the ename to needs.
        '''
        return {variable.ename: variable.sname
                for variable in self.computed_draw.gen_variables()}

    def generate_widget(self):
        self.start_class()

        self.init_method.gen_method()

        template = Template("""
            def __repr__(self):
                return f"<$name {self.name} @ {id(self)}>"

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

    def draw_needed(self):
        return ()

    def clear_calls(self):
        r'''Return True if something was added.
        '''
        return False

class raylib_call(widget):
    vars = (layout, appearance)
    def init(self):
        super().init()
        raylib_call = self.spec.pop('raylib_call')
        self.raylib_fn = raylib_call.pop('name')    # something defined in pyray (raylib) library
        self.raylib_args = raylib_args(raylib_call.pop('args'), self, self.trace)
        if raylib_call:
            print(f"unknown keys in 'raylib_call' section for {self.name}, {tuple(raylib_call.keys())}")

    def output_draw_calls(self, method):
        self.output.print_head(f"{self.raylib_fn}(", first_comma=False)
        for variable in self.raylib_args.gen_variables():
            self.output.print_arg(variable.exp)
        self.output.print_tail(")")

    def draw_needed(self):
        needs = set()
        self.raylib_args.init(self.draw_method, needs)
        return needs

class composite(widget):
    e_x_pos = "getattr(self.x_pos, self.x_align)(self.width)"
    e_y_pos = "getattr(self.y_pos, self.y_align)(self.height)"
    x_pos_arg = "e_x_pos"
    y_pos_arg = "e_y_pos"
    placeholders_allowed = True

    def __init__(self, name, spec, output, trace):
        #print(f"{name}.__init__: {elements=}")
        cls_name = self.__class__.__name__
        cls_section = spec.pop(cls_name)
        self.raw_elements = cls_section.pop('elements')
        if cls_section:
            print(f"unknown keys in {cls_name} section for {name}, "
                  f"{tuple(cls_section.keys())}")
        super().__init__(name, spec, output, trace)    # calls self.init()

    def init(self):
        r'''Called after everything else is initialized in widget.
        '''
        super().init()
        self.elements = []
        self.placeholders = []  # list of placeholder names
        self.element_names = set()
        self.element_widgets = set()

        computed_draw_enames = frozenset(self.computed_draw.gen_names())
        self.needed_draw_names = []
        for elem in self.raw_elements:
            assert len(elem) == 1, f"expected element dict with one key, got {elem=}"
            name, widget_name = elem.copy().popitem()
            if widget_name == "placeholder":
                assert self.placeholders_allowed, f"{self.name}.init: placeholders not allowed"
                self.placeholders.append(name)
                self.elements.append((name, None))
            else:
                widget = Widgets[widget_name]
                self.element_names.add(name)
                self.element_widgets.add(widget_name)
                self.elements.append((name, widget))
                self.needed_draw_names.extend(
                  computed_draw_enames.intersection(
                    (f"{name}__{pname}" for pname in widget.draw_params())))
                self.computed_init.add_create_widget(name, widget_name, f'name=f"{{name}}.{name}"')
        self.sub_init()

    def sub_init(self):
        pass

    def init_calls(self):
        self.output.print_head(f"self.width = {self.width_agg_fn}([", first_comma=False)
        for element in self.element_names:
            self.output.print_arg(f"self.{element}.width")
        for placeholder in self.placeholders:
            self.output.print_arg(f"{placeholder}__width")
        self.output.print_tail('])')
        self.output.print_head(f"self.height = {self.height_agg_fn}([", first_comma=False)
        for element in self.element_names:
            self.output.print_arg(f"self.{element}.height")
        for placeholder in self.placeholders:
            self.output.print_arg(f"{placeholder}__height")
        self.output.print_tail('])')

    def draw_needed(self):
        return self.needed_draw_names

    def output_draw_calls(self, method):
        self.output.print(f"e_x_pos = {self.e_x_pos}")
        self.output.print(f"e_y_pos = {self.e_y_pos}")
        draw_available = self.draw_available()
        for name, widget in self.elements:
            if widget is not None:
                self.output.print_head(f"self.{name}.draw(", first_comma=False)
                self.output.print_arg("x_pos=" + self.x_pos_arg.format(name=name))
                self.output.print_arg("y_pos=" + self.y_pos_arg.format(name=name))
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
        self.layout.add_var('x_align', '"C"')
        self.layout.add_var('y_align', '"C"')

class column(composite):
    e_y_pos = "self.y_pos.S(self.height)"
    width_agg_fn = "max"
    height_agg_fn = "sum"

    def sub_init(self):
        self.layout.add_var('x_align', '"C"')

    def inc_draw_pos(self, sname):
        self.output.print(f"e_y_pos += {sname}.height")

class row(composite):
    e_x_pos = "self.x_pos.S(self.width)"
    width_agg_fn = "sum"
    height_agg_fn = "max"

    def sub_init(self):
        self.layout.add_var('y_align', '"C"')

    def inc_draw_pos(self, sname):
        self.output.print(f"e_x_pos += {sname}.width")

class panel(composite):
    e_x_pos = "self.x_pos.S(self.width)"
    e_y_pos = "self.y_pos.S(self.height)"
    x_pos_arg = "e_x_pos + self.{name}_x_offset"
    y_pos_arg = "e_y_pos + self.{name}_y_offset"
    placeholders_allowed = False

    def init_calls(self):
        pass

class specializes(widget):
    computed_vars = (computed_specialize,)
    methods = (specialize_fn,)
    use_self = False
    use_ename = False

    def init(self):
        super().init()
        self.base_widget = self.spec.pop("specializes")
        self.placeholders = self.spec.pop("placeholders", None)
        self.init_method = specialize_fn(self, self.trace)
        if self.placeholders is not None:
            for placeholder_name, elements in self.placeholders.items():
                for element in elements:
                    name, widget = element.copy().popitem()
                    self.computed_init.add_create_widget(name, widget, f'name=f"{{name}}.{name}"')

    def generate_widget(self):
        self.init_method.gen_method()
        if self.include:
            print("unknown keys in 'include' spec for", self.name, tuple(self.include.keys()))

    def init_calls(self):
        widget_args = ["name=name"]
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
        args, _needs = self.create_widget_args(self.init_method, self.base_widget, "", *widget_args)
        self.output.print_args(f"ans = {self.base_widget}(", args, tail=')', first_comma=False)

    def draw_params(self):
        return Widgets[self.base_widget].draw_params()

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

Widget_types = (raylib_call, stacked, column, row, panel, specializes)
