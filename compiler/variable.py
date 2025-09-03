# variable.py

from translate_exp import translate_exp


__all__ = "param_var computed_exp computed_var computed_create_widget raylib_arg " \
          "pseudo_variable".split()


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
        if self.vars.widget.use_ename and self.vars.use_ename:
            name = self.ename
        if self.vars.widget.use_self:
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
    is_computed = True

    def __init__(self, vars, name, exp):
        super().__init__(vars, name)
        self.exp = exp
        self.needs = set()

    def init(self, method):
        r'''translates exp and adds needs

        Called just prior to generate.
        '''
        self.exp = translate_exp(self.exp, method, self.needs)

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


class raylib_arg(variable):
    is_computed = False

    def __init__(self, vars, name, exp):
        super().__init__(vars, name)
        self.exp = exp

    def init(self, method, needs):
        r'''translates exp and adds needs

        Called just prior to generate.
        '''
        self.exp = translate_exp(self.exp, method, needs)


class pseudo_variable(param):
    r'''Only created by draw_method, so no computed flag needed.
    '''
    def __init__(self, pname, ename, sname, exp=None):
        self.pname = pname
        self.ename = ename
        self.sname = sname
        self.exp = exp

