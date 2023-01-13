#!/usr/bin/python
import functools
import inspect

def trace (_func = None, *, level=1):
    def decorator_trace (func):
        if level > trace .min_level:
            return func
        
        @functools .wraps (func)
        def wrapper (*args, **kwargs):
            trace .count += 1
            print ('_' + '._' * trace .count)
            print (f'TRACE:I{trace .count}: calling {func .__name__} () '
                    f'[[ Argument names:{inspect .signature (func)} ]] '
                    f'with {args}, {kwargs}')

            results = func (*args, **kwargs)

            print (f'TRACE:R{trace.count}: {func .__name__} () '
                    f'has returned')
            print ('*' + '^*' * trace .count)
            trace .count -= 1

            return results 

        return wrapper

    if _func is None:
        return decorator_trace
    else :
        return decorator_trace (_func)


def log (*args, **kwargs):
    if log.DEBUG:
        print ("LOG:", end=' ')
        for v in args:
            print (v, end=' ')
        print (**kwargs)

def progress (*args, **kwargs):
    if not log.DEBUG:
        print ("LOG:", end=' ')
        for v in args:
            print (v, end=' ')
        print (**kwargs)

#SYSTEM RUN PARAMETERS
trace .count = 0
trace .min_level = 1
trace .disabled = True
log .DEBUG = True
