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

    def indent(self):
        self.set_indent(self.current_indent + 4)

    def set_indent(self, i):
        self.current_indent = i
        self.indent_str = ' ' * self.current_indent

    def deindent(self):
        assert self.current_indent >= 4, f"output.deindent: current indent is {self.current_indent} < 4"
        self.set_indent(self.current_indent - 4)

    def print(self, *args, indent=True, sep=' ', end='\n'):
        if args and (len(args) > 1 or args[0]):
            if indent:
                print(self.indent_str, end='', file=self.file)
            print(*args, sep=sep, end=end, file=self.file)
        else:
            print(end=end, file=self.file)

    def print_block(self, text):
        strip = None
        for line in text.splitlines()[1:-1]:
            if strip is None:
                stripped = line.lstrip()
                strip = len(line) - len(stripped)
            self.print(line[strip:])
    def print_args(self, head, args, first_comma=True, tail='):', width=90):
        r'''Head should not end in comma!
        '''
        save_indent = self.current_indent
        self.print(head, end='')
        self.set_indent(self.current_indent + head.index('(') + 1)
        line_len = self.current_indent + len(head)
        if first_comma:
            comma = ', '
        else:
            comma = ''
        for arg in args:
            if line_len + len(comma) + len(arg) > width:
                self.print(comma.rstrip(), indent=False)
                self.print(arg, end='')
                line_len = self.current_indent + len(arg)
            else:
                self.print(comma, arg, indent=False, sep='', end='')
                line_len += len(comma) + len(arg)
            comma = ', '
        self.print(tail, indent=False)
        self.set_indent(save_indent)

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
            words = compile(document, output)
            output.print()
            output.print_args(f"__all__ = (",
                              (f'"{word}"' for word in words + document.get('add_to_all', [])),
                              first_comma=False, tail=')')
            output.print()

Widgets = {}

def compile(document, output):
    words = []
    for name in document.keys():
        if name not in 'module import include add_to_all'.split():
            spec = document[name]
            words.append(name)
            for cls in raylib_call, template, refines:
                cls_name = cls.__name__
                if cls_name in spec:
                    widget = cls(name, spec, output)
                    break
            else:
                for cls in stacked, column, row:
                    cls_name = cls.__name__
                    if cls_name in spec:
                        widget = cls(name, spec, spec[cls_name]['elements'], output)
                        break
                else:
                    raise ValueError(f"compile: unknown spec type for {name=}")
            widget.generate_widget()
            Widgets[name] = widget
    return words

class generator:
    r'''Generates needed computed values.

    Used by computed.generate()
    '''
    def __init__(self, computed, have, needed, trace=False):
        self.trace = trace
        self.computed = computed
        self.seen = set()
        self.have = set(have)
        self.needed = set(needed)
        self.add_needed()
        if self.trace:
            print(f"{self.name()}.__init__: {self.computed.vars=}, {self.have=}, {self.needed=}")

    def name(self):
        return f"{self.computed.widget.name}.{self.__class__.__name__}"

    def generate_all(self):
        self.generate_needed(self.needed, [])

    def generate_needed(self, needed, history):
        if self.trace:
            print(f"{self.name()}.generate_needed: {needed=}, {history=}")
        for name in needed:
            if name not in self.seen and name not in self.have:
                assert name not in history, f"{self.name()}.generate_needed: loop on {name}, {history}"
                history.append(name)
                self.generate(name, history)
        if self.trace:
            print(f"{self.name()}.generate_needed: {needed} done")

    def generate(self, name, history):
        if self.trace:
            print(f"{self.name()}.generate: {name=}, {history=}")
        if name in self.computed:
            locals, exp = self.computed[name]
            self.generate2(name, locals, exp, history)
            return
        raise AssertionError(f"{self.name()}.generate: don't know how to compute {name}, {self.seen=}")

    def generate2(self, name, locals, exp, history):
        if self.trace:
            print(f"{self.name()}.generate2: {name=}, {locals=}, {exp=}")
        self.generate_needed(locals, history)
        if self.trace:
            print(f"{self.name()}.generate2: outputing {name=}, {locals=}, {exp=}")
        self.seen.add(name)
        self.output(name, locals, exp)

    def add_needed(self):
        pass

class init_generator(generator):
    def add_needed(self):
        self.needed.update(self.computed.var_names())

    def output(self, name, locals, exp):
        self.computed.widget.output.print(f"self.{name} = ", end='')
        self.computed.widget.output.print(exp, indent=False)

class draw_generator(generator):
    def output(self, name, locals, exp):
        self.computed.widget.output.print(f"{name} = ", end='')
        self.computed.widget.output.print(exp, indent=False)

class vars:
    r'''This encapsulates {name: exp} dicts in the yaml file.

    The dicts are the raw yaml data.  They have not been processed or converted.

    Created by widget.__init__.
    '''
    def __init__(self, vars, widget, trace=False):
        self.trace = trace
        self.vars = vars
        self.widget = widget
        self.output = self.widget.output
        self.init()

    def __contains__(self, name):
        ans = name in self.vars
        #print(f"vars.__contains__({name}) -> {ans}")
        return ans

    def keys(self):
        return self.vars.keys()

    def values(self):
        return self.vars.values()

    def items(self):
        return self.vars.items()

    def __getitem__(self, name):
        #print(f"{self.__class__.__name__}.__getitem__({name!r})")
        return self.vars[name]

    def __setitem__(self, name, value):
        #print(f"{self.__class__.__name__}.__getitem__({name!r})")
        self.vars[name] = value

    def var_names(self):
        return self.vars.keys()

    def map_names(self, fn):
        return [fn(name) for name in self.vars.keys()]

    def map_items(self, fn):
        return [fn(name, exp) for name, exp in self.vars.items()]

    def init(self):
        pass

class params(vars):
    pass

class layout(params):
    pass

class appearance(params):
    pass

class shortcuts(vars):
    def substitution(self, var):
        if var in self.vars:
            return self.vars[var]
        return var

class computed(vars):
    simple_added = ()
    composite_added = ()
    added = ()
    initialized = False

    def check_delayed_init(self, method):
        if not self.initialized:
            self.delayed_init(method)
            self.initialized = True

    def delayed_init(self, method):
        r'''Extend self.vars with self.added and do translate_exp on all exps.  And expand element
        names on all names.
        '''
        new_vars = {}
        if isinstance(self.widget, composite):
            added = self.added + self.composite_added
        else:
            added = self.added + self.simple_added
        for name, exp in chain(self.vars.items(), added):
            # element.b.c -> element__b.c
            tname = method.translate_name(name, sub_shortcuts=False, add_self=False)
            if tname not in new_vars:
                new_vars[tname] = method.translate_exp(exp)
        self.vars = new_vars

    def generate(self, have, needed, method, trace=False):
        r'''This may be called multiple times.

        Called from method class.
        '''
        self.check_delayed_init(method)
        needed = set(needed)
        self.generator(self, have, needed, trace).generate_all()

class computed_init(computed):
    simple_added = (('max_width', 'width'),
                    ('max_height', 'height'),
                   )
    generator = init_generator

class computed_draw(computed):
    added = (('x_left', 'x_pos.S(width).i'),
             ('x_center', 'x_pos.C(width).i'),
             ('x_right', 'x_pos.E(width).i'),
             ('y_top', 'y_pos.S(height).i'),
             ('y_middle', 'y_pos.C(height).i'),
             ('y_bottom', 'y_pos.E(height).i'),
            )
    generator = draw_generator

class method:
    word_re = r'[.\w]+=?'
    global_names = frozenset("str int float self and or not math round min max sum as_dict "
                             "half measure_text_ex".split())
    first_auto_params = {}
    final_auto_params = {}

    def __init__(self, widget, trace=False):
        self.trace = trace
        self.widget = widget
        self.locals = None
        for name in 'layout appearance computed_init computed_draw output'.split():
            setattr(self, name, getattr(widget, name))
        if self.trace:
            print(f"{self.__class__.__name__}.__init__({self.widget})")

    def translate_name(self, name, sub_shortcuts=True, add_self=True):
        r'''Translates names:
           
           - .a.b    -> unchanged
           - s[.a.b]                            where s is shortcut -> x[.a.b] where x is substitution
           - e.a.b   -> e__a.b                  where e is element_name
           - f[.a.b] -> f added to self.locals  where f isidentifier, f[0] not upper, and
                                                       not in global_names
           - x.a.b   -> self.x.a.b              where x in element_names or 
                                                       (add_self and x in layout or computed_init)
        '''
        if isinstance(name, re.Match):
            name = name.group(0)
        if name[0] == '.' or name[-1] == '=':
            return name
        names = name.split('.', 1)
        if sub_shortcuts:
            expanded = self.widget.shortcuts.substitution(names[0]).split('.')
            names = expanded + names[1:]
        if names[0] in self.widget.element_names and len(names) > 1:
            names[0: 2] = [f"{names[0]}__{names[1]}"]

        # add to self.locals?
        if self.locals is not None:
            first = names[0]
            if first.isidentifier() and not first[0].isupper() and first not in self.global_names:
                self.locals.add(first)

        if add_self and (names[0] in self.widget.element_names or
                         names[0] in self.widget.layout or
                         names[0] in self.widget.appearance or
                         names[0] in self.widget.computed_init):
            names.insert(0, 'self')
        return '.'.join(names)

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

    def generate(self):
        self.start()           # prints def __init__(...):
        self.output.indent()
        self.body()            # assignments
        self.end()             # final if trace: and as_sprite init
        self.output.deindent()
        self.output.print()

    def start(self):
        params = self.get_params()
        self.output.print_args(f"def {self.method_name}(self",
                               (f"{name}={exp}" for name, exp in params.items()))

    def copy_param(self, name):
        r'''outputs the lines in the body to copy param name.
        '''
        # element.foo -> element__foo
        pname = self.translate_name(name, sub_shortcuts=False, add_self=False)

        # also substitutes shortcuts: short -> long
        sname = self.translate_name(name, add_self=False)

        self.output_copy(pname, sname)

    def get_first_auto_params(self):
        return self.first_auto_params

    def get_final_auto_params(self):
        return self.final_auto_params

    def get_params(self):
        first_auto_params = self.get_first_auto_params()
        final_auto_params = self.get_final_auto_params()
        params = first_auto_params.copy()
        for vars in self.param_vars:
            params.update(self.as_params(getattr(self, vars)))
        params.update(final_auto_params)
        self.params = params
        return params

    def body(self):
        # e.a.b -> e__a.b
        param_names = tuple(self.translate_name(name, sub_shortcuts=False, add_self=False)
                            for name in self.params.keys())
        for name in param_names:
            self.copy_param(name)
        # e.a.b -> e__a.b
        # s.a.b -> x.a.b
        have = set(self.translate_name(name, add_self=False)
                   for name in self.params.keys())
        self.load_have(have)
        if self.trace:
            print(f"{self.__class__.__name__}.body({self.widget.name}): have={have}")
        self.gen_computed(have)
        # end takes care of if trace and if as_sprite

    def load_have(self, have):
        pass

class init_method(method):
    method_name = '__init__'
    first_auto_params = dict(as_sprite=False, dynamic_capture=False)
    final_auto_params = dict(trace=False)
    param_vars = 'layout', 'appearance'

    def get_first_auto_params(self):
        params = dict(name=f'"a {self.widget.name}"')
        params.update(self.first_auto_params)
        return params

    def as_params(self, vars):
        r'''Returns a list of (name, default) pairs ready for dict.
        '''
        return vars.map_items(
                 lambda name, exp:
                   # the only useful thing this translate_name does is translate element.foo names
                   # to element__foo.
                   (f"{self.translate_name(name, sub_shortcuts=False, add_self=False)}", exp))

    def output_copy(self, pname, sname):
        self.output.print(f"self.{sname} = {pname}")

    def gen_computed(self, have):
        if isinstance(self.widget, composite):
            needed = set()
        else:
            needed = set(('max_width', 'max_height'))

        # force generation of all computed names so that draw has access to them too.
        needed.update(self.translate_name(name, sub_shortcuts=False, add_self=False)
                      for name in self.computed_init.var_names())

        self.computed_init.generate(have, needed, self, self.trace)

    def end(self):
        self.output.print("if trace:")
        self.output.indent()
        args = ', '.join(f'{{self.{name}=}}' for name in self.appearance.var_names())
        self.output.print(f'print(f"{self.widget.name}({{self.name}}).__init__: {args}")')
        self.output.deindent()
        self.widget.init_calls()
        self.output.print_block("""
            if self.as_sprite:
                self.sprite = sprite.Sprite(self.max_width, self.max_height, dynamic_capture, self.trace)
        """)

class draw_method(method):
    method_name = 'draw'
    first_auto_params = dict(x_pos=False, y_pos=False)
    param_vars = 'appearance',

    def as_params(self, vars):
        r'''Returns a list of (name, None) pairs ready for dict.
        '''
        return vars.map_names(
                 lambda name:
                   # the only useful thing this translate_name does is translate element.foo names
                   # to element__foo.
                   (f"{self.translate_name(name, sub_shortcuts=False, add_self=False)}", None))

    def load_have(self, have):
        r'''Loads have with anything beyond parameters.
        '''
        have.update(self.layout.var_names())
        have.update(self.computed_init.var_names())

    def gen_computed(self, have):
        self.computed_draw.generate(have, self.widget.draw_needed(), self, self.trace)

    def output_copy(self, pname, sname):
        template = Template("""
            if $pname is None:
                $pname = self.$sname
            else:
                self.$sname = $pname
        """)
        self.output.print_block(template.substitute(pname=pname, sname=sname))

    def end(self):
        self.output.print("if self.trace:")
        self.output.indent()
        args = ', '.join(f'{{{name}}}=' for name in self.appearance.var_names())
        self.output.print(f'print(f"{self.widget.name}({{self.name}}).draw: {args}")')
        self.output.deindent()
        self.output.print_block("""
            if self.as_sprite:
                self.sprite.save_pos(self.x_pos, self.y_pos)
        """)
        self.widget.output_draw_calls(self)

class widget:
    element_names = ()
    element_widgets = ()

    def __init__(self, name, spec, output):
        self.trace_init = spec.get('trace_init', False)
        self.trace_draw = spec.get('trace_draw', False)
        self.name = name
        self.spec = spec
        self.output = output
        for section, trace in (layout, False), (appearance, False), (shortcuts, False):
            name = section.__name__
            setattr(self, name, section(spec.get(name, {}), self, trace))
        computed = spec.get('computed', {})
        for section, trace in (computed_init, False), (computed_draw, False):
            name = section.__name__
            subname = name[9:]
            #print(f"{self.__class__.__name__}({self.name}).__init__: {name=}, {subname=}")
            setattr(self, name, section(computed.get(subname, {}), self, trace))
        self.init()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def init(self):
        pass

    def generate_widget(self):
        self.start_class()

        init_method(self, self.trace_init).generate()

        template = Template("""
            def __repr__(self):
                return f"<$name {self.name} @ {self.id()}>"

        """)
        self.output.print_block(template.substitute(name=self.name))

        draw_method(self, self.trace_draw).generate()

        self.end_class()

    def start_class(self):
        self.output.print(f"class {self.name}:")
        self.output.indent()

    def end_class(self):
        self.output.deindent()

    def init_calls(self):
        pass

class raylib_call(widget):
    def init(self):
        raylib_call = self.spec['raylib_call']
        self.raylib_fn = raylib_call['name']
        self.raylib_args = raylib_call['args']

    def output_draw_calls(self, method):
        args = ', '.join(method.translate_name(name) for name in self.raylib_args)
        self.output.print(f"{self.raylib_fn}({args})")

    def draw_needed(self):
        return self.raylib_args

class composite(widget):
    def __init__(self, name, spec, elements, output):
        print(f"{name}.__init__: {elements=}")
        self.element_names = frozenset(elements.keys())
        self.element_widgets = frozenset(elements.values())
        self.elements = {name: Widgets[widget] for name, widget in elements.items()}
        super().__init__(name, spec, output)

    def init(self):
        for element, widget in self.elements.items():
            needed_names = []
            def check_name(name, exp, my_vars):
                if self.trace_init:
                    print(f"{self.name}.init: {name=}, {exp=}")
                if name not in 'as_sprite dynamic_capture'.split():
                    compound_name = f"{element}__{name}"
                    dotted_name = f"{element}.{name}"
                    def name_ok(name):
                        return name not in my_vars and \
                               name not in self.computed_init and \
                               name not in self.shortcuts.values()
                    if name_ok(compound_name) and name_ok(dotted_name):
                        my_vars[compound_name] = exp
                    needed_names.append(compound_name)
            for vars in 'layout', 'appearance':
                if self.trace_init:
                    print(f"{self.name}.init: {element=}, {widget=}, {vars=}")
                my_vars = getattr(self, vars)
                getattr(widget, vars).map_items(partial(check_name, my_vars=my_vars))
            check_name('name', f'"a {element}"', self.layout)
            check_name('trace', False, self.layout)
            if self.trace_init:
                print(f"{self.name}.init: {needed_names=}")
            element_args = []
            for name in needed_names:
                if name.startswith(element + '__'):
                    element_args.append(f"{name[len(element) + 2:]}={name}")
                else:
                    element_args.append(f"{name}={name}")
            self.computed_init[element] = f"{widget.name}({', '.join(element_args)})"

class stacked(composite):
    pass

class column(composite):
    pass

class row(composite):
    pass

class refines(widget):
    def generate_widget(self):
        self.output.print(f"# {self.name} refines")

class template(widget):
    def generate_widget(self):
        self.output.print(f"# {self.name} template")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file")

    args = parser.parse_args()

    read_yaml(args.yaml_file)

