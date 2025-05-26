# doctest_exc.py


def exc_notes(*notes):
    r'''

        >>> exc_notes()
        Traceback (most recent call last):
            ...
        AttributeError: 'function' object has no attribute 'foobar'

        >>> exc_notes('hello world')
        Traceback (most recent call last):
            ...
        AttributeError: 'function' object has no attribute 'foobar'
        hello world

        >>> exc_notes('hello world')    # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        AttributeError: 'function' object has no attribute 'foobar'
        ...

        >>> try:
        ...     exc_notes('hello world')    # doctest: +ELLIPSIS
        ... except AttributeError as e:
        ...     print(str(e))
        'function' object has no attribute 'foobar'

    '''
    try:
        exc_notes.foobar
    except AttributeError as e:
        for note in notes:
            e.add_note(note)
        raise


def exc_cause():
    r'''

        >>> exc_cause()
        Traceback (most recent call last):
            ...
        AttributeError: second errorr

    '''
    try:
        exc_cause.foobar
    except AttributeError as e:
        #raise AttributeError(f"second error")
        raise AttributeError(f"second error") from e


if __name__ == "__main__":
    import doctest
    doctest.testmod()
