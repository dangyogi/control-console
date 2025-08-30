# vars.py

import re
from functools import partial

from tsort import *
from variable import *


__all__ = "layout appearance computed_init computed_specialize computed_draw shortcuts".split()


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

        Only called by translate_exp.
        '''
        if isinstance(name, re.Match):
            name = name.group(0)
        if name[0] == '.' or name[-1] in '(=':
            return name
        names = name.split('.', 1)
        first = names[0]
        if sub_shortcuts:
            first = names[0] = self.widget.shortcuts.substitute(first)
            if self.trace:
                print(f"translate_name({name=}): after shortcuts.substitute, {first=}")
        if names[0] in self.widget.element_names and len(names) > 1:
            first = f"{names[0]}__{names[1]}"
            if self.trace:
                print(f"translate_name({name=}): after element_name__, {names=}, {first=}")
            names[0: 2] = [first]

        # add to self.locals?
        if self.locals is not None and first in self:
            if self.trace:
                print(f"translate_name({name=}): adding to locals, {first=}")
            self.locals.add(first)

        ans = '.'.join(names)
        if add_self and (first in self.widget.element_names or
                         first in self.widget.layout or
                         first in self.widget.appearance or
                         first in self.widget.computed_init):
            ans = 'self.' + ans
            if self.trace:
                print(f"translate_name({name=}): adding 'self.', {ans=}")
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
    name = "layout"

class appearance(params):
    name = "appearance"

class computed(vars):
    added = ()
    locals = None
    sub_shortcuts = True
    add_self = True

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
        self.inames[iname] = None

    def init2(self):
        r'''This is run by widget.__init__ after both computed_init/draw have been __init__-ed

        Which means that they'll have their inames figured out, but not their needed or translated
        exps when this is called.
        '''
        if self.trace:
            print(f"{self.__class__.__name__}.init2 providing:")
            for iname, exp in sorted(self.vars2.items()):
                print(f"  {iname}: {exp}")
        self.snames = {}
        for iname, exp in self.vars2.items():
            var = self.var_class(self.widget, iname, *self.translate_exp(exp))
            if self.trace:
                print(f"{self.__class__.__name__}.init2: {var=}")
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
        exp = first + re.sub(self.word_re,
                             partial(self.translate_name,
                                     sub_shortcuts=self.sub_shortcuts,
                                     add_self=self.add_self),
                             rest)
        locals = self.locals
        self.locals = None
        if self.trace:
            print(f"{self.__class__.__name__}.translate_exp -> {locals=}, {exp=}")
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
    name = "computed_init"

class computed_specialize(computed_init):
    generator = draw_generator
    sub_shortcuts = False
    add_self = False

class computed_draw(computed):
    name = "computed_draw"
    added = (('draw_height', 'height'),
             ('draw_width', 'width'),

             ('x_left', 'x_pos.S(draw_width).i'),
             ('x_center', 'x_pos.C(draw_width).i'),
             ('x_right', 'x_pos.E(draw_width).i'),
             ('y_top', 'y_pos.S(draw_height).i'),
             ('y_middle', 'y_pos.C(draw_height).i'),
             ('y_bottom', 'y_pos.E(draw_height).i'),
            )
    generator = draw_generator
    var_class = draw_var

    def init(self, vars):
        super().init(vars)
        self.inames = {name: None for name in self.vars2.keys()}

class shortcuts:
    r'''Only used to translate shortcut pnames to expanded inames.

    Used by params.init, vars.translate_name and specializes.widget_exp
    '''
    name = "shortcuts"

    def __init__(self, vars, widget, trace=False):
        self.widget = widget
        self.trace = trace

        # {pname: iname}
        self.pnames = {shortcut.replace('.', '__'): iname.replace('.', '__')
                       for shortcut, iname in vars.items()}

        # {iname: pname}
        self.inames = {iname: pname for pname, iname in self.pnames.items()}

    def substitute(self, pname):
        return self.pnames.get(pname, pname)

    def desubstitute(self, iname):
        return self.inames.get(iname, iname)

