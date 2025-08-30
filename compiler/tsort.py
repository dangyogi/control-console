# tsort.py


__all__ = "init_generator draw_generator".split()


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
