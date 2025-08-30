# variable.py


__all__ = "param_var computed_var init_var draw_var".split()


class variable:
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

    def __repr__(self):
        return f"<{self.__class__.__name__}: pname={self.pname}, iname={self.iname}, " \
               f"sname={self.sname}, needs={self.needs}, exp={self.exp}>"

class param_var(variable):
    def init(self, name, exp):
        self.pname = name.replace('.', '__')
        self.iname = self.widget.shortcuts.substitute(self.pname)
        self.needs = ()
        self.exp = exp

class computed_var(variable):
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

