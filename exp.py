# exp.py

r'''Expressions.

Expressions start with one of the following three special letters:

    I - refers to the current instance.  Much like "self" within a function.
    T - refers to the surrounding template instance.  Much like the module containing the function.
    F - refers to standard python functions, e.g, F.str

After seeing any of these, any of the these things following it are baked into an expression object for
later evaluation/execution:

    fn_calls: exp(...)
    numeric expressions:
        -exp
        exp + b
        exp - b
        exp * b
        exp / b
        exp // b
        ... and all of the reverse versions, e.g., b + exp
    exp.name

The exp's are later evaluated by a context (see context.py).
'''

import operator
import builtins

import context
from alignment import *


__all__ = tuple('ITF') + ('eval_exp',)


Trace = False


def eval_exp(x, instance, template=None):
    if isinstance(x, exp):
        return x.eval(instance, template)
    return x

class exp:
    r'''This is the base class of all exp's.  It handles creating bigger exp's out smaller ones.

        >>> I.foobar
        I.foobar
        >>> I.foo + 7 * -I.bar - 12 - 3*7
        I.foo + 7 * -I.bar - 12 - 21
        >>> (I.foo + 7) * (-I.bar - 12) - 3*7
        (I.foo + 7) * (-I.bar - 12) - 21
        >>> I.foo + 1 + 2 + 3
        I.foo + 1 + 2 + 3
        >>> I.foo * 1 * 2 * 3
        I.foo * 1 * 2 * 3
    '''
    def __call__(self, *args, **kwargs):
        r'''Doesn't support functions returning exp's.

            >>> I.foo(2, 3)
            I.foo(2, 3)
        '''
        return call(self, args, kwargs)

    def __neg__(self):
        r'''
            >>> -I.foo
            -I.foo
        '''
        return unop(self, operator.neg, '-')

    def __add__(self, b):
        r'''
            >>> I.foo + 4
            I.foo + 4
        '''
        return binop(self, b, operator.add, '+', 10)

    def __sub__(self, b):
        r'''
            >>> I.foo - 4
            I.foo - 4
        '''
        return binop(self, b, operator.sub, '-', 10)

    def __mul__(self, b):
        r'''
            >>> I.foo * 4
            I.foo * 4
        '''
        return binop(self, b, operator.mul, '*', 20)

    def __truediv__(self, b):
        r'''
            >>> I.foo / 4
            I.foo / 4
        '''
        return binop(self, b, operator.truediv, '/', 20)

    def __floordiv__(self, b):
        r'''
            >>> I.foo // 4
            I.foo // 4
        '''
        return binop(self, b, operator.floordiv, '//', 20)

    def __radd__(self, b):
        r'''
            >>> 4 + I.foo
            4 + I.foo
        '''
        return binop(b, self, operator.add, '+', 10)

    def __rsub__(self, b):
        r'''
            >>> 4 - I.foo
            4 - I.foo
        '''
        return binop(b, self, operator.sub, '-', 10)

    def __rmul__(self, b):
        r'''
            >>> 4 * I.foo
            4 * I.foo
        '''
        return binop(b, self, operator.mul, '*', 20)

    def __rtruediv__(self, b):
        r'''
            >>> 4 / I.foo
            4 / I.foo
        '''
        return binop(b, self, operator.truediv, '/', 20)

    def __rfloordiv__(self, b):
        r'''
            >>> 4 // I.foo
            4 // I.foo
        '''
        return binop(b, self, operator.floordiv, '//', 20)

    def __getattr__(self, name):
        r'''
            >>> I.foo.bar
            I.foo.bar
        '''
        return exp_getattr(self, name)

class exp_I(exp):
    r'''Returns the current instance.
    '''
    prec = 100

    def __repr__(self):
        return "I"

    def eval(self, instance, template):
        return instance

I = exp_I()

class exp_T(exp):
    r'''Returns the current template (e.g., template param instance).
    '''
    prec = 100

    def __repr__(self):
        return "T"

    def eval(self, instance, template):
        assert template is not None, f"T used outside of template"
        return template

T = exp_T()

class exp_F(exp):
    r'''Returns the current instance.
    '''
    prec = 100

    def __getattr__(self, name):
        return global_getter(name)  # needs to return an exp to continue building the exp

F = exp_F()

class global_getter(exp):
    prec = 93
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"F.{self.name}"

    def eval(self, instance, template):
        try:
            return globals()[self.name]
        except KeyError:
            return getattr(builtins, self.name)

class call(exp):
    prec = 90

    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        head = f"{self.fn}({', '.join((str(arg) for arg in self.args))}"
        if self.kwargs:
            return head + f", {', '.join((f'{name}={value}' for name, value in self.kwargs.items()))})"
        return head + ')'

    def eval(self, instance, template):
        r'''Doesn't support functions returning exp's.
        '''
        fn = eval_exp(self.fn, instance, template)
        args = [eval_exp(arg, instance, template) for arg in self.args]
        kwargs = {key: eval_exp(value, instance, template) for key, value in self.kwargs.items()}
        return fn(*args, **kwargs)

class unop(exp):
    prec = 80

    def __init__(self, a, op, sym):
        self.a = a
        self.op = op
        self.sym = sym

    def __repr__(self):
        return f"{self.sym}{self.a}"

    def eval(self, instance, template):
        a_i = eval_exp(self.a, instance, template)
        return self.op(a_i)

class binop(exp):
    def __init__(self, a, b, op, sym, prec):
        self.a = a
        self.b = b
        self.op = op
        self.sym = sym
        self.prec = prec

    def __repr__(self):
        if not isinstance(self.a, exp):
            a_prec = 100
        else:
            a_prec = self.a.prec
        if a_prec < self.prec:
            a_repr = f"({self.a!r})"
        else:
            a_repr = repr(self.a)

        if not isinstance(self.b, exp):
            b_prec = 100
        else:
            b_prec = self.b.prec
        if b_prec <= self.prec:
            b_repr = f"({self.b!r})"
        else:
            b_repr = repr(self.b)

        return f"{a_repr} {self.sym} {b_repr}"

    def eval(self, instance, template):
        a_i = eval_exp(self.a, instance, template)
        b_i = eval_exp(self.b, instance, template)
        return self.op(a_i, b_i)

class exp_getattr(exp):
    prec = 93

    def __init__(self, obj, name):
        self.obj = obj
        self.name = name

    def __repr__(self):
        return f"{self.obj}.{self.name}"

    def eval(self, instance, template):
        if Trace:
            print(f"exp_getattr.eval: {self.obj=}, {instance=}, {template=}")
        obj = eval_exp(self.obj, instance, template)
        if Trace:
            print(f"... {self.obj=} evals to {obj=}")
        value = getattr(obj, self.name)
        if Trace:
            print(f"exp_getattr.eval: {self.obj=}, {obj=}, {self.name=}, {value=}")
        if isinstance(obj, context.instance):
            if Trace:
                print(f"... obj is instance, calling eval_exp")
            ans = eval_exp(value, obj, obj if isinstance(obj, context.template) else template)
            if Trace:
                print(f"... got {ans=}")
            return ans
        assert not isinstance(value, exp), \
               f"unexpected exp from {self.obj=} in {obj=}.{self.name}, {type(obj)=}, {context.instance=}"
        return value



if __name__ == "__main__":
    import doctest
    if Trace:
        doctest.testmod(verbose=True)
    else:
        doctest.testmod()
