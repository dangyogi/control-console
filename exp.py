# exp.py

r'''Expressions.

Expressions start with one of the following three special letters:

    I - refers to the current Drawable instance.  Much like "self" within a method.
    P - refers to the surrounding Composite instance.  Much like the module containing the function.
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

The exp's are later evaluated by eval_exp.
'''

import sys
import operator
import builtins

from alignment import *   # so F can find these in globals()


__all__ = "I P F eval_exp".split()


Trace = False


def eval_exp(x, instance, level=0, trace=False):
    if isinstance(x, Exp):
        if Trace or trace:
            print(f"{' ' * level}eval_exp: {x}, {instance=}", file=sys.stderr)
        ans = x.eval(instance, level, trace)
        if Trace or trace:
            print(f"{' ' * level}eval_exp: {ans=}", file=sys.stderr)
        return ans
    return x


class Exp:
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
        r'''Doesn't support functions returning Exp's.

            >>> I.foo(2, 3)
            I.foo(2, 3)
        '''
        return call(self, args, kwargs)

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

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

class exp_I(Exp):
    r'''Returns the current Drawable instance.
    '''
    prec = 100

    def __repr__(self):
        return "I"

    def eval(self, instance, level, trace):
        return instance

I = exp_I()

class exp_P(Exp):
    r'''Returns the current Composite (e.g., the current instance's parent).
    '''
    prec = 100

    def __repr__(self):
        return "P"

    def eval(self, instance, level, trace):
        parent = instance.parent
        if parent is None:
            raise AttributeError(f"P used outside of Composite")
        #if Trace or trace or instance.exp_trace:
        #    print(f"{' ' * level}exp_P got {parent=}", file=sys.stderr)
        return parent

P = exp_P()

class exp_F(Exp):
    r'''Returns the a global variable (usually a function, hence, F).
    '''
    prec = 100

    def __getattr__(self, name):
        return global_getter(name)  # needs to return an Exp to continue building the exp

F = exp_F()

class global_getter(Exp):
    r'''Tries globals().name, then builtins.name.

    Used by exp_F.
    '''
    prec = 93
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"F.{self.name}"

    def eval(self, instance, level, trace):
        try:
            return globals()[self.name]
        except KeyError:
            return getattr(builtins, self.name)

class call(Exp):
    r'''Does a function call.
    '''
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

    def eval(self, instance, level, trace):
        r'''Doesn't support functions returning Exp's.
        '''
        fn = eval_exp(self.fn, instance, level + 1, trace)
        args = [eval_exp(arg, instance, level + 1, trace) for arg in self.args]
        kwargs = {key: eval_exp(value, instance, level + 1, trace) for key, value in self.kwargs.items()}
        return fn(*args, **kwargs)

class unop(Exp):
    r'''Evaluates an unary operator.
    '''
    prec = 80

    def __init__(self, a, op, sym):
        self.a = a
        self.op = op
        self.sym = sym

    def __repr__(self):
        return f"{self.sym}{self.a}"

    def eval(self, instance, level, trace):
        a_i = eval_exp(self.a, instance, level + 1, trace)
        return self.op(a_i)

class binop(Exp):
    r'''Evaluates a binary operator.
    '''
    def __init__(self, a, b, op, sym, prec):
        self.a = a
        self.b = b
        self.op = op
        self.sym = sym
        self.prec = prec

    def __repr__(self):
        if not isinstance(self.a, Exp):
            a_prec = 100
        else:
            a_prec = self.a.prec
        if a_prec < self.prec:
            a_repr = f"({self.a!r})"
        else:
            a_repr = repr(self.a)

        if not isinstance(self.b, Exp):
            b_prec = 100
        else:
            b_prec = self.b.prec
        if b_prec <= self.prec:
            b_repr = f"({self.b!r})"
        else:
            b_repr = repr(self.b)

        return f"{a_repr} {self.sym} {b_repr}"

    def eval(self, instance, level, trace):
        a_i = eval_exp(self.a, instance, level + 1, trace)
        b_i = eval_exp(self.b, instance, level + 1, trace)
        return self.op(a_i, b_i)

class exp_getattr(Exp):
    r'''Gets an attribute off of an object.  The object is another expression.
    '''
    prec = 93

    def __init__(self, obj, name):
        self.obj = obj
        self.name = name

    def __repr__(self):
        return f"{self.obj}.{self.name}"

    def eval(self, instance, level, trace):
        if Trace or trace or instance.exp_trace:
            print(f"{' ' * level}exp_getattr: {self.obj=}, {self.name=}, {instance=} "
                  "-> eval_exp(self.obj)",
                  file=sys.stderr)
        obj = eval_exp(self.obj, instance, level + 1, trace)
        #if Trace or trace or instance.exp_trace:
        #    print(f"{' ' * level} {self.obj=} evals to {obj=}", file=sys.stderr)
        if isinstance(obj, drawable.Drawable):
            raw_value = getattr(obj, self.name)
            if Trace or trace or instance.exp_trace:
                print(f"{' ' * level}obj is Drawable, {raw_value=}, calling eval_exp", file=sys.stderr)
            ans = eval_exp(raw_value, obj, level + 1, trace)
            if Trace or trace or instance.exp_trace:
                print(f"{' ' * level}got {ans=}", file=sys.stderr)
            return ans

        value = getattr(obj, self.name)
        if Trace or trace or instance.exp_trace:
            print(f"{' ' * level}exp_getattr: {obj=}.{self.name} -> {value=}", file=sys.stderr)

        assert not isinstance(value, Exp), \
               f"unexpected Exp from {self.obj=} in {obj=}.{self.name}, {type(obj)=}"
        return value

import drawable


if __name__ == "__main__":
    import doctest
    if Trace:
        doctest.testmod(verbose=True)
    else:
        doctest.testmod()
