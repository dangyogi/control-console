# indenter.py


class indenter:
    def __init__(self, file, width=94):
        self.file = file
        self.width = width
        self.current_indent = 0
        self.indent_str = ''
        self.need_indent = True

    def indent(self):
        self.set_indent(self.current_indent + 4)

    def set_indent(self, i):
        self.current_indent = i
        self.indent_str = ' ' * self.current_indent

    def deindent(self):
        assert self.current_indent >= 4, f"output.deindent: current indent is {self.current_indent} < 4"
        self.set_indent(self.current_indent - 4)

    def print(self, *args, sep=' ', end='\n'):
        if args and (len(args) > 1 or args[0]):
            if self.need_indent:
                print(self.indent_str, end='', file=self.file)
            print(*args, sep=sep, end=end, file=self.file)
            if end:
                self.need_indent = end[-1] == '\n'
            elif args:
                self.need_indent = args[-1][-1] == '\n'
        else:
            print(end=end, file=self.file)
            self.need_indent = end[-1] == '\n'

    def print_block(self, text):
        strip = None
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if (i == 0 or i == len(lines) - 1) and not line.strip():
                continue
            if strip is None:
                stripped = line.lstrip()
                strip = len(line) - len(stripped)
            self.print(line[strip:])

    def print_args(self, head, args, first_comma=True, tail='):'):
        r'''Head should not end in comma!
        '''
        self.print_head(head, first_comma)
        for arg in args:
            self.print_arg(arg)
        self.print_tail(tail)

    def print_head(self, head, first_comma=True):
        self.print(head, end='')
        self.line_len = self.current_indent + len(head)
        self.save_indent = self.current_indent
        self.set_indent(self.current_indent + head.index('(') + 1)
        if first_comma:
            self.comma = ', '
        else:
            self.comma = ''

    def print_arg(self, arg):
        if self.line_len + len(self.comma) + len(arg) > self.width and \
           self.line_len > self.current_indent:
            # arg won't fit on current line
            self.print(self.comma.rstrip())   # ends the current line
            self.print(arg, end='')           # starts the next line at self.current_indent
            self.line_len = self.current_indent + len(arg)
        else:
            self.print(self.comma, arg, sep='', end='')
            self.line_len += len(self.comma) + len(arg)
        self.comma = ', '

    def print_tail(self, tail):
        self.print(tail)
        self.set_indent(self.save_indent)

