# tsort.py


#__all__ = "init_generator draw_generator".split()


def tsort(vars, needed, trace):
    r'''yields all needed variables in vars in a sequence that satisfies their needs constraints.

    Raises AssertionError if needs loops or unable to fill a need.

    trace is a list of names.
    '''
    seen = set()
    needed = set(needed)
    history = []

    def name():
        return f"{vars.widget.name}.tsort({vars.__class__.__name__})"

    def generate_needed(needed):
        for needed_name in needed:
            if needed_name not in seen:
                if "generate_needed" in trace:
                    print(f"generate_needed: {needed_name=} not in {seen=}, {history=} ...")
                assert needed_name not in history, f"{name()}: loop on {needed_name}, {history}"
                history.append(needed_name)
                if needed_name in vars:
                    variable = vars[needed_name]
                    if "generate_needed" in trace:
                        print(f"generate_needed: {needed_name=}, "
                              f"calling generated_needed({variable.needs=})")
                    yield from generate_needed(variable.needs)
                    seen.add(needed_name)
                    if "generate_needed" in trace:
                        print(f"generate_needed: {needed_name=}, yielding {variable.ename=}")
                    yield variable
                else:
                    raise AssertionError(
                            f"{name()}.generate: don't know how to compute {needed_name}, {seen=}")

    if "tsort" in trace:
        print(f"tsort calling generate_needed({needed=})")
    return generate_needed(needed)

