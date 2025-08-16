# compiler.py

import re
from string import Template
from itertools import chain

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
    def print_args(self, head, args, tail='):', width=90):
        r'''Head should not end in comma!
        '''
        save_indent = self.current_indent
        self.print(head, end='')
        self.set_indent(self.current_indent + head.index('(') + 1)
        line_len = self.current_indent + len(head)
        for arg in args:
            if line_len + 2 + len(arg) > width:
                self.print(',', indent=False)
                self.print(arg, end='')
                line_len = self.current_indent + len(arg)
            else:
                self.print(', ', arg, indent=False, sep='', end='')
                line_len += 2 + len(arg)
        self.print(tail, indent=False)
        self.set_indent(save_indent)

def process(document):
    if 'module' in document:
        filename = document['module'] + '.py'
        with open(filename, 'x') as out_file:
            output = indenter(out_file)
            output.print("#", filename)
            output.print()
            if 'import' in document:
                for imp in document['import']:
                    output.print(imp)
                output.print()
            if 'include' in document:
                text = document['include'].rstrip()
                output.print(text)
                output.print()
            compile(document, output)

def compile(document, output):
    for name in document.keys():
        if name not in 'module import include'.split():
            spec = document[name]
            if 'raylib_call' in spec:
                compile_raylib_call(name, spec, output)
            elif 'stacked' in spec or 'column' in spec or 'row' in spec:
                compile_composite(name, spec, output)
            else:
                compile_placeholder(name, spec, output)

class generator:
    r'''Generates needed computed values.
    '''
    def __init__(self, computed, have, needed, trace=False):
        self.trace = trace
        self.computed = computed
        self.seen = set()
        self.have = set(have)
        self.needed = set(needed)
        self.add_needed()
        if self.trace:
            print(f"{self.name()}.__init__: {self.computed=}, {self.have=}, {self.needed=}")

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
    '''
    def __init__(self, vars, widget, output, trace=False):
        self.trace = trace
        self.vars = vars
        self.widget = widget
        self.output = output
        self.init()

    def __contains__(self, name):
        ans = name in self.vars
        #print(f"vars.__contains__({name}) -> {ans}")
        return ans

    def __getitem__(self, name):
        return self.vars[name]

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
    added = ()
    initialized = False

    def generate(self, have, needed, trace=False):
        r'''This may be called multiple times.
        '''
        if not self.initialized:
            new_vars = {}
            for name, exp in chain(self.vars.items(), self.added):
                if name not in new_vars:
                    new_vars[name] = self.widget.translate_exp(exp)
            self.vars = new_vars
            self.initialized = True
        self.generator(self, have, needed, trace).generate_all()

class computed_init(computed):
    added = (('max_width', 'width'),
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
    def __init__(self, widget, trace=False):
        self.trace = trace
        self.widget = widget
        for name in 'layout appearance computed_init computed_draw output'.split():
            setattr(self, name, getattr(widget, name))
        if self.trace:
            print(f"{self.__class__.__name__}.__init__({self.widget})")

    def generate(self):
        self.start()       # prints def __init__(...):
        self.output.indent()
        self.body()        # assignments
        self.end()         # final if trace: and as_sprite init
        self.output.deindent()
        self.output.print()

class init_method(method):
    def start(self):
        self.auto_args = "name as_sprite dynamic_capture".split()
        args = [f"name='a {self.widget.name}'", "as_sprite=False", "dynamic_capture=False"]
        args.extend(self.as_args(self.layout))
        args.extend(self.as_args(self.appearance))
        args.append("trace=False")
        self.output.print_args("def __init__(self", args)

    def as_args(self, vars):
        r'''Returns a list of "name=default" for __init__ params
        '''
        return vars.map_items(lambda name, exp:
                                f"{self.widget.translate_name(name, add_self=False)}={exp}")

    def init_name(self, name):
        tname = self.widget.translate_name(name, add_self=False)
        self.output.print(f"self.{tname} = {tname}")

    def body(self):
        self.init_name("trace")
        self.init_name("name")
        self.init_name("as_sprite")
        self.layout.map_names(self.init_name)
        self.appearance.map_names(self.init_name)
        have = chain(self.auto_args, self.layout.var_names(), self.appearance.var_names())
        if self.trace:
            have = tuple(have)
            print(f"init_method({self.widget.name}): {have=}")
        self.computed_init.generate(have, ('max_width', 'max_height'), self.trace)
        #self.computed_draw.generate(have, ('max_width', 'max_height'), self.trace)

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
    def __init__(self, widget, trace=False):
        super().__init__(widget, trace)
        self.args = ["x_pos", "y_pos"]
        self.args.extend(self.appearance.var_names())

    def start(self):
        self.output.print_args("def draw(self", [x + '=None' for x in self.args])

    def body(self):
        for arg in self.args:
            self.init_var(arg)
        have = chain(self.args, self.layout.var_names(), self.computed_init.var_names())
        if self.trace:
            have = tuple(have)
            print(f"draw_method({self.widget.name}): {have=}")
        #self.computed_init.generate(have, self.widget.draw_needed())
        self.computed_draw.generate(have, self.widget.draw_needed(), self.trace)

    def init_var(self, name):
        template = Template("""
            if $name is None:
                $name = self.$name
            else:
                self.$name = $name
        """)
        tname = self.widget.translate_name(name, add_self=False)
        self.output.print_block(template.substitute(name=tname))

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
        self.widget.draw_calls()

class widget:
    element_names = ()
    word_re = r'[.\w]+'
    global_names = frozenset("str int float self and or not math round as_dict "
                             "half measure_text_ex".split())

    def __init__(self, name, spec, output):
        self.trace_init = spec.get('trace_init', False)
        self.trace_draw = spec.get('trace_draw', False)
        self.name = name
        self.spec = spec
        self.output = output
        self.locals = None
        for section, trace in (layout, False), (appearance, False), (shortcuts, False):
            name = section.__name__
            setattr(self, name, section(spec.get(name, {}), self, output, trace))
        computed = spec.get('computed', {})
        for section, trace in (computed_init, False), (computed_draw, False):
            name = section.__name__
            subname = name[9:]
            #print(f"{self.__class__.__name__}({self.name}).__init__: {name=}, {subname=}")
            setattr(self, name, section(computed.get(subname, {}), self, output, trace))
        self.init()

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

    def translate_name(self, name, add_self=True):
        if isinstance(name, re.Match):
            name = name.group(0)
        if name[0] == '.':
            return name
        names = name.split('.', 1)
        expanded = self.shortcuts.substitution(names[0]).split('.')
        names = expanded + names[1:]
        if names[0] in self.element_names and len(names) > 1:
            names[0: 2] = [f"{names[0]}__{names[1]}"]

        # add to self.locals?
        if self.locals is not None:
            first = names[0]
            if first.isidentifier() and not first[0].isupper() and first not in self.global_names:
                self.locals.add(first)

        if names[0] in self.element_names \
           or (add_self and (names[0] in self.layout or names[0] in self.computed_init)):
            names.insert(0, 'self')
        return '.'.join(names)

    def translate_exp(self, exp):
        r'''Does the following:

        - does shortcut substitution for first name in a.b.c
        - converts element.foo to element__foo
        - adds self. to vars in layout or computed_init

        Returns a list of local words referenced, updated exp text.
        '''
        if not isinstance(exp, str):
            return [], exp
        self.locals = set()  # locals passed back to translate_exp through self.locals...
        exp = re.sub(self.word_re, self.translate_name, exp)
        locals = self.locals
        self.locals = None
        return locals, exp

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

    def draw_calls(self):
        args = ', '.join(self.translate_name(name) for name in self.raylib_args)
        self.output.print(f"{self.raylib_fn}({args})")

    def draw_needed(self):
        return self.raylib_args

def compile_raylib_call(name, spec, output):
    widget = raylib_call(name, spec, output)
    widget.generate_widget()

def fix_dot_refs(var_dict, dunder, with_locals=False):
    ans = {}
    for name, exp in var_dict.items():
        name = dunder(name)
        local_refs, exp = decode_exp(exp, dunder)
        if with_locals:
            ans[name] = local_refs, exp
        elif local_refs:
            raise AssertionError(f"fix_dot_refs: locals not allowed in {name=}: {exp=}")
        else:
            ans[name] = exp
    return ans

def make_arg(name, default):
    return f"{name}={default}"

def compile_composite(name, spec, output):
    output.print("#", name, "composite")
    output.print()

def compile_placeholder(name, spec, output):
    output.print("#", name, "placeholder")
    output.print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("yaml_file")

    args = parser.parse_args()

    read_yaml(args.yaml_file)

