# compiler.py

import re
from string import Template
from itertools import chain
from functools import partial

from yaml import safe_load_all


def read_yaml(yaml_filename):
    with open(yaml_filename, "r") as yaml_file:
        for document in safe_load_all(yaml_file):
            process(document)

class indenter:
    def __init__(self, file):
        self.file = file
        self.current_indent = 0
        self.indent_str = ''
        self.need_indent = True

    def indent(self):
        self.set_indent(self.current_indent + 4)

    def set_indent(self, i):
        self.current_indent = i
        self.indent_str = ' ' * self.current_indent

    def deindent(self):
        assert self.current_indent >= 4, f"output.deindent: current indent is {self.current_indent} < 4"
        self.set_indent(self.current_indent - 4)

    def print(self, *args, sep=' ', end='\n'):
        if args and (len(args) > 1 or args[0]):
            if self.need_indent:
                print(self.indent_str, end='', file=self.file)
            print(*args, sep=sep, end=end, file=self.file)
            if end:
                self.need_indent = end[-1] == '\n'
            elif args:
                self.need_indent = args[-1][-1] == '\n'
        else:
            print(end=end, file=self.file)
            self.need_indent = end[-1] == '\n'

    def print_block(self, text):
        strip = None
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if (i == 0 or i == len(lines) - 1) and not line.strip():
                continue
            if strip is None:
                stripped = line.lstrip()
                strip = len(line) - len(stripped)
            self.print(line[strip:])

    def print_args(self, head, args, first_comma=True, tail='):', width=94):
        r'''Head should not end in comma!
        '''
        self.print_head(head, first_comma, width=width)
        for arg in args:
            self.print_arg(arg)
        self.print_tail(tail)

    def print_head(self, head, first_comma=True, width=94):
        self.print(head, end='')
        self.line_len = self.current_indent + len(head)
        self.save_indent = self.current_indent
        self.set_indent(self.current_indent + head.index('(') + 1)
        if first_comma:
            self.comma = ', '
        else:
            self.comma = ''
        self.width = width

    def print_arg(self, arg):
        if self.line_len + len(self.comma) + len(arg) > self.width:
            # arg won't fit on current line
            self.print(self.comma.rstrip())   # ends the current line
            self.print(arg, end='')           # starts the next line at self.current_indent
            self.line_len = self.current_indent + len(arg)
        else:
            self.print(self.comma, arg, sep='', end='')
            self.line_len += len(self.comma) + len(arg)
        self.comma = ', '

    def print_tail(self, tail):
        self.print(tail)
        self.set_indent(self.save_indent)

def process(document):
    if 'module' in document:
        filename = document['module'] + '.py'
        with open(filename, 'w') as out_file:
            output = indenter(out_file)
            output.print("#", filename)
            output.print()
            if 'import' in document:
                for imp in document['import']:
                    output.print(imp)
                output.print()
                output.print()
            if 'include' in document:
                text = document['include'].rstrip()
                output.print(text)
                output.print()
            if 'widget_stubs' in document:
                for name, args in document['widget_stubs'].items():
                    Widgets[name] = widget_stub(name, layout=args.get('layout', ()),
                                                      appearance=args.get('appearance', ()))
            words = compile(document, output)
            output.print()
            output.print_head(f"__all__ = (", first_comma=False)
            for word in words + document.get('add_to_all', []):
                output.print_arg(f'"{word}"')
            output.print_tail(')')
            output.print()

Widgets = {}

def compile(document, output):
    words = []
    for name in document.keys():
        if name not in 'module import include add_to_all widget_stubs'.split():
            spec = document[name]
            if spec.get('skip', False):
                continue
            print()
            print("compiling", name)
            words.append(name)
            spec_copy = spec.copy()
            for cls in raylib_call, specializes:
                cls_name = cls.__name__
                if cls_name in spec_copy:
                    widget = cls(name, spec_copy, output)
                    break
            else:
                for cls in stacked, column, row:
                    cls_name = cls.__name__
                    if cls_name in spec_copy:
                        #print(f"compile {name=}, {cls_name=}, {spec[cls_name]=}")
                        cls_section = spec_copy.pop(cls_name)
                        elements = cls_section.pop('elements')
                        if cls_section:
                            print(f"unknown keys in {cls_name} section for {name}, "
                                  f"{tuple(cls_section.keys())}")
                        widget = cls(name, spec_copy, elements, output)
                        break
                else:
                    raise ValueError(f"compile: unknown spec type for {name=}")
            widget.generate_widget()
    return words

class generator:
    r'''Generates needed computed values.

    Used by computed.gen_vars().

    Can only be used once.
    '''
    def __init__(self, computed, needed, trace=False):
        self.trace = trace
        self.computed = computed
        self.seen = set()
        self.needed = set(needed)
        self.add_needed()
        if self.trace:
            print(f"{self.name()}.__init__: {self.computed.gen_inames()=}, {self.needed=}")

    def name(self):
        return f"{self.computed.widget.name}.{self.__class__.__name__}"

    def generate_all(self):
        self.generate_needed(self.needed, [])

    def generate_needed(self, needed, history):
        if self.trace:
            print(f"{self.name()}.generate_needed: {needed=}, {history=}")
        for iname in needed:
            if iname not in self.seen:
                assert iname not in history, f"{self.name()}.generate_needed: loop on {iname}, {history}"
                history.append(iname)
                self.generate_computed(iname, history)
        if self.trace:
            print(f"{self.name()}.generate_needed: {needed} done")

    def generate_computed(self, iname, history):
        if self.trace:
            print(f"{self.name()}.generate_computed: {iname=}, {history=}")
        if iname in self.computed:
            var = self.computed[iname]
            self.generate(iname, var.needs, var.exp, history)
            return
        raise AssertionError(f"{self.name()}.generate: don't know how to compute {iname}, {self.seen=}")

    def generate(self, iname, needs, exp, history):
        if self.trace:
            print(f"{self.name()}.generate: {iname=}, {needs=}, {exp=}")
        self.generate_needed(needs, history)
        if self.trace:
            print(f"{self.name()}.generate2: outputing {iname=}, {exp=}")
        self.seen.add(iname)
        self.output(iname, exp)

    def add_needed(self):
        pass

class init_generator(generator):
    def add_needed(self):
        self.needed.update(self.computed.gen_inames())

    def output(self, iname, exp):
        self.computed.widget.output.print(f"self.{iname} =", exp)

class draw_generator(generator):
    def output(self, iname, exp):
        self.computed.widget.output.print(f"{iname} =", exp)

class var:
    r'''Has:

      - pname: param name in method parameter list)
      - iname: internal name in the body of the method, without "self."
      - sname: internal name with "self." (if needed)
      - needs: only for computed vars, these are inames
      - exp: ready for output
    '''
    pname = None
    sname_prefix = "self."

    def __init__(self, widget, name, exp):
        self.widget = widget
        self.init(name, exp)
        self.sname = self.sname_prefix + self.iname

class param_var(var):
    def init(self, name, exp):
        self.pname = name.replace('.', '__')
        self.iname = self.widget.shortcuts.substitute(self.pname)
        self.needs = ()
        self.exp = exp

class computed_var(var):
    def __init__(self, widget, iname, needs, exp):
        self.needs = set(needs)
        super().__init__(widget, iname, exp)

    def init(self, name, exp):
        self.iname = name
        self.exp = exp

class init_var(computed_var):
    pass

class draw_var(computed_var):
    sname_prefix = ""

class vars:
    r'''This encapsulates {name: exp} dicts in the yaml file.

    The dicts are the raw yaml data.  They have not been processed or converted.

    Created by widget.__init__.
    '''
    word_re = r'[.\w]+[(=]?'
    global_names = frozenset("str int float self and or not math round min max sum as_dict "
                             "half measure_text_ex".split())
    pnames = {}

    def __init__(self, vars, widget, trace=False):
        self.trace = trace
        self.vars = vars
        self.widget = widget
        self.output = self.widget.output
        self.init(vars)  # creates self.pnames, self.inames and self.snames

    def init2(self):
        pass

    def __contains__(self, iname):
        ans = iname in self.inames
        #print(f"vars.__contains__({iname}) -> {ans}")
        return ans

    def gen_pnames(self):
        return self.pnames.keys()

    def gen_inames(self):
        return self.inames.keys()

    def gen_snames(self):
        return self.snames.keys()

    #def values(self):
    #    return self.vars.values()

    #def items(self):
    #    return self.vars.items()

    def __getitem__(self, iname):
        #print(f"{self.__class__.__name__}.__getitem__({iname!r})")
        return self.inames[iname]

    def add_var(self, var):
        self.pnames[var.pname] = var
        self.inames[var.iname] = var
        self.snames[var.sname] = var

    #def __setitem__(self, iname, value):
    #    #print(f"{self.__class__.__name__}.__getitem__({iname!r})")
    #    self.inames[iname] = value

    def map_pnames(self, fn):
        r'''Calls fn successively with each pname.

        Return a list of fn returns.
        '''
        return [fn(pname) for pname in self.pnames.keys()]

    def map_inames(self, fn):
        r'''Calls fn successively with each iname.

        Return a list of fn returns.
        '''
        return [fn(iname) for iname in self.inames.keys()]

    def map_pitems(self, fn):
        r'''Calls fn successively with each pname, var.

        Return a list of fn returns.
        '''
        return [fn(pname, var) for pname, var in self.pnames.items()]

    def map_iitems(self, fn):
        r'''Calls fn successively with each iname, var.

        Return a list of fn returns.
        '''
        return [fn(iname, var) for iname, var in self.inames.items()]

    def translate_name(self, name, sub_shortcuts=True, add_self=True):
        r'''Translates names:
           
           - a(      -> unchanged               a is function, we don't use function params
           - a=      -> unchanged               a is keyword param for some other function
           - .a.b    -> unchanged               .a.b comes after something other than an identifier
           - s[.a.b]                            where s is shortcut -> x[.a.b] where x is substitution
           - s__a[.b]                           where s is shortcut -> x__a[.b] where x is substitution
           - e.a.b   -> e__a.b                  where e is element_name
           - f[.a.b] -> f added to self.locals  where f in self
           - x.a.b   -> self.x.a.b              where add_self and translated x in
                                                        element_names, layout, appearance or
                                                        computed_init inames
        '''
        if isinstance(name, re.Match):
            name = name.group(0)
        if name[0] == '.' or name[-1] in '(=':
            return name
        names = name.split('.', 1)
        first = names[0]
        if sub_shortcuts:
            first = names[0] = self.widget.shortcuts.substitute(first)
        if names[0] in self.widget.element_names and len(names) > 1:
            first = f"{names[0]}__{names[1]}"
            names[0: 2] = [first]

        # add to self.locals?
        if self.locals is not None and first in self:
            self.locals.add(first)

        ans = '.'.join(names)
        if add_self and (first in self.widget.element_names or
                         first in self.widget.layout or
                         first in self.widget.appearance or
                         first in self.widget.computed_init):
            ans = 'self.' + ans
        return ans

class params(vars):
    def init(self, vars):
        self.pnames = {}
        self.inames = {}
        self.snames = {}
        for name, exp in vars.items():
            var = param_var(self.widget, name, exp)
            self.pnames[var.pname] = var
            self.inames[var.iname] = var
            self.snames[var.sname] = var

class layout(params):
    pass

class appearance(params):
    pass

class computed(vars):
    added = ()
    locals = None

    def init(self, vars):
        # translate_exp needs this fully loaded with names before doing any exp translations.
        # that's why we split the actual initialization of self.var_class into a second init phase.
        self.vars2 = dict(self.added)  # {iname: exp}
        self.vars2.update(vars)  # overrides added
        self.inames = {name: None for name in self.vars2.keys()}

    def add_compute(self, iname, exp):
        r'''This needs to happen before init2 is called!  See widget.__init__
        '''
        self.vars2[iname] = exp

    def init2(self):
        r'''This is run by widget.__init__ after both computed_init/draw have been __init__-ed

        Which means that they'll have their inames figured out, but not their needed or translated
        exps when this is called.
        '''
        self.snames = {}
        for iname, exp in self.vars2.items():
            var = self.var_class(self.widget, iname, *self.translate_exp(exp))
            self.inames[var.iname] = var
            self.snames[var.sname] = var

    def translate_exp(self, exp):
        r'''Does the following:

        - does shortcut substitution for first name in a.b.c
        - converts element.foo to element__foo
        - adds self. to vars in layout, appearances or computed_init

        Returns a list of local words referenced, updated exp text.

        Only used by computed:
        '''
        if not isinstance(exp, str):
            return [], exp
        dquote_index = exp.find('"')
        squote_index = exp.find("'")
        if dquote_index >= 0 or squote_index >= 0:
            if dquote_index >= 0 and (squote_index < 0 or dquote_index < squote_index):
                quote = '"'
            else: # dquote_index < 0 or squote_index >=0 and dquote_index >= squote_index
                quote = "'"
            parts = exp.split(quote)
            all_locals = set()
            for i in range(0, len(parts), 2):
                locals, new_part = self.translate_exp(parts[i])
                parts[i] = new_part
                all_locals.update(locals)
            return list(all_locals), quote.join(parts)
        self.locals = set()  # locals passed back to translate_exp through self.locals...
        first = ''
        rest = exp
        if self.trace:
            print(f"{self.__class__.__name__}.translate_exp: checking {exp=}")
        for name in self.widget.element_widgets:
            if exp.startswith(f"{name}("):
                first = exp[:len(name) + 1]
                rest = exp[len(name) + 1:]
                if self.trace:
                    print(f"{self.__class__.__name__}.translate_exp: "
                          f"starts with element={name}, {first=}, {rest=}")
                break
        exp = first + re.sub(self.word_re, self.translate_name, rest)
        locals = self.locals
        self.locals = None
        return locals, exp

    def gen_vars(self, needed, method, trace=False):
        r'''This may be called multiple times.

        Called from method class.
        '''
        needed = set(needed)
        self.generator(self, needed, trace).generate_all()

class computed_init(computed):
    generator = init_generator
    var_class = init_var

class computed_draw(computed):
    added = (('draw_height', 'height'),
             ('draw_width', 'width'),

             ('x_left', 'x_pos.S(draw_width)'),
             ('x_center', 'x_pos.C(draw_width)'),
             ('x_right', 'x_pos.E(draw_width)'),
             ('y_top', 'y_pos.S(draw_height)'),
             ('y_middle', 'y_pos.C(draw_height)'),
             ('y_bottom', 'y_pos.E(draw_height)'),
            )
    generator = draw_generator
    var_class = draw_var

class shortcuts:
    r'''Only used to translate shortcut pnames to expanded inames.

    By params.init and vars.translate_name
    '''
    def __init__(self, vars, widget, trace=False):
        self.widget = widget
        self.trace = trace
        self.pnames = {shortcut.replace('.', '__'): iname.replace('.', '__')
                       for shortcut, iname in vars.items()}

    def substitute(self, pname):
        if '__' in pname:
            first, rest = pname.split('__', 1)
            rest = '__' + rest
        else:
            first = pname
            rest = ''
        return self.pnames.get(first, first) + rest

class method:
    first_auto_params = {}

    def __init__(self, widget, trace=False):
        self.trace = trace
        self.widget = widget
        for name in 'layout appearance computed_init computed_draw output'.split():
            setattr(self, name, getattr(widget, name))
        if self.trace:
            print(f"{self.__class__.__name__}.__init__({self.widget}): "
                  f"get_params()={self.get_params()}")

    def gen_method(self):
        self.start()           # prints def __init__(...):
        self.output.indent()
        self.body()            # assignments
        self.end()             # final if trace: and include, etc init
        self.output.deindent()
        self.output.print()

    def start(self):
        self.params = self.get_params()  # list of (pname, iname, sname, exp)
        self.output.print_args(f"def {self.method_name}(self",
                               (f"{pname}={exp}" for pname, _, _, exp in self.params))

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
        for pname, _, sname, _ in self.params:
            self.output_copy(pname, sname)
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

    def output_copy(self, pname, sname):
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
        else:
            self.output.print(f"{sname} = {pname}")

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

    def output_copy(self, pname, sname):
        template = Template("""
            if $pname is not None:
                $sname = $pname
        """)
        self.output.print_block(template.substitute(pname=pname, sname=sname))

    def end(self):
        self.output.print("if self.trace:")
        self.output.indent()
        args = ', '.join(f'{{{sname=}}}' for sname in self.appearance.gen_snames())
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


class widget:
    element_names = ()     # element names, excluding placeholders
    element_widgets = ()   # widget names, excluding placeholders, used by translate_exp

    def __init__(self, name, spec, output):
        self.spec = spec
        self.trace_init = self.spec.pop('trace_init', False)
        self.trace_draw = self.spec.pop('trace_draw', False)
        self.name = name
        self.output = output
        self.include = self.spec.pop('include', {})
        for section, trace in (shortcuts, False), (layout, False), (appearance, False):
            name = section.__name__
            setattr(self, name, section(self.spec.pop(name, {}), self, trace))
        computed = self.spec.pop('computed', {})
        for section, trace in (computed_init, False), (computed_draw, False):
            name = section.__name__
            subname = name[9:]
            #print(f"{self.__class__.__name__}({self.name}).__init__: {name=}, {subname=}")
            setattr(self, name, section(computed.pop(subname, {}), self, trace))
        if computed:
            print("unknown keys in 'computed' spec for", self.name, tuple(self.computed.keys()))
        self.init_method = init_method(self, self.trace_init)
        self.draw_method = draw_method(self, self.trace_draw)
        self.clear_method = clear_method(self)
        Widgets[self.name] = self
        self.init()  # may override assignment to Widgets and add_compute to computed_init/draw...
        for section_name in "computed_init", "computed_draw":
            getattr(self, section_name).init2()
        if self.trace_init:
            print(f"widget({self.name}).__init__: {self.init_params()=}")
        if self.trace_draw:
            print(f"widget({self.name}).__init__: {self.draw_params()=}")
        if self.spec:
            print("unknown keys in spec for", self.name, tuple(self.spec.keys()))

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def init(self):
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

    def __init__(self, name, spec, elements, output):
        #print(f"{name}.__init__: {elements=}")
        self.raw_elements = elements
        super().__init__(name, spec, output)    # calls self.init()

    def init(self):
        r'''Called after everything else is initialized in widget.
        '''
        self.elements = []
        self.placeholders = []
        self.needed_draw_names = []
        self.element_names = set()
        self.element_widgets = set()
        computed_draw_inames = frozenset(self.computed_draw.gen_inames())
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
                self.needed_draw_names.extend(
                  computed_draw_inames.intersection(
                    (f"{name}__{pname}" for pname in widget.draw_params())))
                init_available = self.init_available_inames()  # set(iname)
                init_params = (f"{name}__{pname}" for pname in widget.init_params().keys())
                params_to_pass = init_available.intersection(init_params)
                args_to_pass = [f"{my_iname[len(name) + 2:]}={my_iname}" 
                                for my_iname in params_to_pass]
                name_pname = f"{name}__name"
                if name_pname not in params_to_pass:
                    args_to_pass.insert(0, f'name="{name}"')
                    if self.trace_init:
                        print(f"added name {name=}, {name_pname=}, {args_to_pass[0]=}")
                self.computed_init.add_compute(
                   name,
                   f"{widget_name}({', '.join(args_to_pass)})"
                )
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
    def init(self):
        self.base_widget = self.spec.pop("specializes")
        self.placeholders = self.spec.pop("placeholders", None)

    def generate_widget(self):
        self.output.print(f"# {self.name} specializes")

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



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file")

    args = parser.parse_args()

    read_yaml(args.yaml_file)

