# variable.py

import re


__all__ = "param_var computed_exp computed_var computed_create_widget pseudo_variable".split()


class variable:
    r'''Has:

      - pname: param name and name used in yaml file, exps, and in generated funs.  Only param_vars
               have pnames.
      - ename: expanded child__name, child__grandchild__name
      - sname: storage name (with "self.", can be used in any method to refer to same value)
      - needs: only for computed vars, these are vnames
      - exp: ready for output
    '''
    is_computed = False

    def __init__(self, vars, name):
        self.vars = vars
        self.ename = self.vars.widget.shortcuts.substitute(name)
        if self.vars.use_ename:
            name = self.ename
        if self.vars.use_self:
            self.sname = "self." + name
        else:
            self.sname = name

    def __repr__(self):
        if hasattr(self, 'exp'):
            return f"<{self.__class__.__name__}: ename={self.ename}, sname={self.sname}, exp={self.exp}>"
        return f"<{self.__class__.__name__}: ename={self.ename}, sname={self.sname}>"

class param:
    computed = False

    def as_param(self):
        return f"{self.pname}={self.exp}"

    def load(self, method):
        if not self.computed:
            method.load_param(self)

class param_var(variable, param):
    needs = ()

    def __init__(self, vars, name, exp):
        self.pname = name
        self.exp = exp
        super().__init__(vars, name)

    def flag_computed(self):
        self.computed = True

class computed_exp(variable):
    word_re = r'[.\w]+[(=]?'

    # FIX: still needed?
    global_names = frozenset("str int float self and or not math round min max sum as_dict "
                             "half measure_text_ex".split())
    is_computed = True

    def __init__(self, vars, name, exp):
        super().__init__(vars, name)
        self.exp = exp
        self.needs = set()

    def init(self, method):
        r'''translates exp and adds needs

        Called just prior to generate.
        '''
        self.exp = self.translate_exp(self.exp)

    def translate_name(self, name):
        r'''Translates names:

           - a(      -> unchanged               a is function, we don't use function params
           - a=      -> unchanged               a is keyword param for some other function
           - .a.b    -> unchanged               .a.b comes after something other than an identifier
           - s[.a.b]                            where s is shortcut -> x[.a.b] where x is substitution
           - s__a[.b]                           where s is shortcut -> x__a[.b] where x is substitution
           - e.a.b   -> e__a.b                  where e is element_name
           - f[.a.b] -> f added to self.needs   where f in self
           - x.a.b   -> self.x.a.b              where use_self and translated x in
                                                        element_names, layout, appearance or
                                                        computed_init inames

        Only called by translate_exp.
        '''
        if isinstance(name, re.Match):
            name = name.group(0)
        if name[0] == '.' or name[-1] in '(=':
            return name
        names = name.split('.', 1)
        first = names[0]
        first = names[0] = self.vars.widget.shortcuts.substitute(first)
        if "translate_name" in self.vars.trace:
            print(f"translate_name({name=}): after shortcuts.substitute, {first=}")
        if names[0] in self.vars.widget.element_names and len(names) > 1:
            first = f"{names[0]}__{names[1]}"
            if "translate_name" in self.vars.trace:
                print(f"translate_name({name=}): after element_name__, {names=}, {first=}")
            names[0: 2] = [first]

        # first is now ename
        if first in self.vars:
            if "translate_name" in self.vars.trace:
                print(f"translate_name({name=}): adding to needs, {first=}")
            self.needs.add(first)

        if self.vars.use_self and first in self.vars.widget.element_names:
            first = 'self.' + first
            if "translate_name" in self.vars.trace:
                print(f"translate_name({name=}): adding 'self.' to element name, {first=}")
        elif first in self.vars.widget.layout:
            first = self.vars.widget.layout[first].sname
            if "translate_name" in self.vars.trace:
                print(f"translate_name({name=}): using layout sname, {first=}")
        elif first in self.vars.widget.appearance:
            first = self.vars.widget.appearance[first].sname
            if "translate_name" in self.vars.trace:
                print(f"translate_name({name=}): using appearance sname, {first=}")
        elif first in self.vars:
            first = self.vars[first].sname
            if "translate_name" in self.vars.trace:
                print(f"translate_name({name=}): using self.vars sname, {first=}")
        names[0] = first
        return '.'.join(names)

    def translate_exp(self, exp):
        r'''Does the following:

        - does shortcut substitution for first name in a.b.c
        - converts element.foo to element__foo
        - adds self. to vars in layout, appearances or computed_init
        - adds references to self.vars to self.needs

        Returns updated exp text.

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
            for i in range(0, len(parts), 2):
                parts[i] = self.translate_exp(parts[i])
            return quote.join(parts)
        first = ''
        rest = exp
        if "translate_exp" in self.vars.trace:
            print(f"{self.__class__.__name__}.translate_exp: checking {exp=}")
        for name in self.vars.widget.element_widgets:
            if exp.startswith(f"{name}("):
                first = exp[:len(name) + 1]  # incl '('
                rest = exp[len(name) + 1:]
                if "translate_exp" in self.vars.trace:
                    print(f"{self.__class__.__name__}.translate_exp: "
                          f"starts with element={name}, {first=}, {rest=}")
                break
        exp = first + re.sub(self.word_re, self.translate_name, rest)
        if "translate_exp" in self.vars.trace:
            print(f"{self.__class__.__name__}.translate_exp -> {exp=}")
        return exp

class computed_var(computed_exp):
    computed_param = False

    def __init__(self, vars, name, exp):
        super().__init__(vars, name, exp)

        # check for computed_param:
        param = None
        if name in vars.widget.layout:
            param = vars.widget.layout[name]
            where = "layout"
        elif name in vars.widget.appearance:
            param = vars.widget.appearance[name]
            where = "appearance"
        if param is not None:
            if param.exp is not None:
                print(f"{vars.widget.name}.computed_var({name}): "
                      f"ERROR: also in {where} with a non-None exp {param.exp}")
            param.flag_computed()
            self.computed_param = True
            self.pname = param.pname
            if "computed_var" in self.vars.trace:
                print(f"{self.__class__.__name__}.__init__({name=}): setting computed_param")

    def load(self, method):
        if self.computed_param:
            method.load_computed_param(self)
        else:
            method.load_computed(self)

class computed_create_widget(variable):
    r'''These can not be created in the yaml computed: section.

    They are only created internally to the compiler.
    '''
    is_computed = True

    def __init__(self, vars, child_name, widget_name, args):
        super().__init__(vars, child_name)
        self.child_name = child_name
        self.widget_name = widget_name
        self.args_init = args

    def init(self, method):
        r'''gathers arguments
        '''
        self.args, self.needs = \
          self.vars.widget.create_widget_args(method, self.widget_name,
                                              f"{self.child_name}__", *self.args_init)

    def load(self, method):
        method.load_create_widget(self)  # head is "sname = widget_name(", figured out by method


class pseudo_variable(param):
    r'''Only created by draw_method, so no computed flag needed.
    '''
    def __init__(self, pname, ename, sname, exp=None):
        self.pname = pname
        self.ename = ename
        self.sname = sname
        self.exp = exp

