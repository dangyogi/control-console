# translate_exp.py

import re
from functools import partial



def translate_name(name, method, needs):
    r'''Translates names:

       - a(      -> unchanged               a is function, we don't use function params
       - a=      -> unchanged               a is keyword param for some other function
       - .a.b    -> unchanged               .a.b comes after something other than an identifier
       - s[.a.b]                            where s is shortcut -> x[.a.b] where x is substitution
       - s__a[.b]                           where s is shortcut -> x__a[.b] where x is substitution
    no - e.a.b   -> e__a.b                  where e is element_name
       - f[.a.b] -> f added to needs        where f in getattr(widget, method.computed_vars)
       - x.a.b   -> self.x.a.b              where use_self and translated x in
                                                    element_names, layout, appearance,
                                                    computed_init, or computed_vars enames

    Only called by translate_exp.
    '''
    if isinstance(name, re.Match):
        name = name.group(0)
    if name[0] == '.' or name[-1] in '(=':
        return name
    names = name.split('.', 1)
    first = names[0]
    first = names[0] = method.widget.shortcuts.substitute(first)
    if "translate_name" in method.trace:
        print(f"translate_name({name=}): after shortcuts.substitute, {first=}")

    # first is now ename

    if "translate_name" in method.trace:
        print(f"translate_name({name=}): {method.computed_vars_name=}")
    if method.computed_vars_name is not None:
        computed_vars = getattr(method.widget, method.computed_vars_name)
        if first in computed_vars:
            if "translate_name" in method.trace:
                print(f"translate_name({name=}): in method.computed_vars_name, "
                      f"adding to needs, {first=}")
            needs.add(first)
    else:
        computed_vars = ()
        if first in method.widget.computed_init:
            if "translate_name" in method.trace:
                print(f"translate_name({name=}): in computed_init, adding to needs, {first=}")
            needs.add(first)

    if method.widget.use_self and first in method.widget.element_names:
        first = 'self.' + first
        if "translate_name" in method.trace:
            print(f"translate_name({name=}): adding 'self.' to element name, {first=}")
    else:
        available_variables = {variable.ename: variable
                               for variable in method.available_variables()}
        if first in available_variables:
            first = available_variables[first].sname
            if "translate_name" in method.trace:
                print(f"translate_name({name=}): using method.available_variables sname, {first=}")

    names[0] = first
    return '.'.join(names)


Word_re = r'\w+((\.\w+)*|[(=])'  # matches \w+ (.\w+)* or, \w+(=

#Global_names = frozenset("str int float self and or not math round min max sum as_dict "
#                         "half measure_text_ex".split())

def translate_exp(exp, method, needs):
    r'''Does the following:

    - does shortcut substitution for first name in a.b.c
    - converts element.foo to element__foo
    - adds self. to vars in layout, appearances or computed_init
    - adds references to method.computed_vars to needs

    Returns updated exp text.

    Only used by computed:
    '''
    if not isinstance(exp, str):
        return exp
    dquote_index = exp.find('"')
    squote_index = exp.find("'")
    if dquote_index >= 0 or squote_index >= 0:
        if dquote_index >= 0 and (squote_index < 0 or dquote_index < squote_index):
            quote = '"'
        else: # dquote_index < 0 or squote_index >=0 and dquote_index >= squote_index
            quote = "'"
        parts = exp.split(quote)
        for i in range(0, len(parts), 2):
            parts[i] = translate_exp(parts[i], method, needs)
        return quote.join(parts)
    first = ''
    rest = exp
    if "translate_exp" in method.trace:
        print(f"translate_exp: checking {exp=}")
    for name in method.widget.element_widgets:
        if exp.startswith(f"{name}("):
            first = exp[:len(name) + 1]  # incl '('
            rest = exp[len(name) + 1:]
            if "translate_exp" in method.trace:
                print(f"translate_exp: starts with element={name}, {first=}, {rest=}")
            break
    exp = first + re.sub(Word_re,
                         partial(translate_name, method=method, needs=needs),
                         rest)
    if "translate_exp" in method.trace:
        print(f"translate_exp -> {exp=}")
    return exp

