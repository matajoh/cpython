# Send/Receive

The goal of this work is to add Erlang-like send and receive capabilities
to subinterpreters. To begin, this requires adding two new builtins to the
language:

```python
def send(interp: InterpreterID, obj: Any):
"""Send obj to the target interpreter.

Args:
    interp: The ID of the target interpreter
    obj: Any sendable object

Raises:
    Shutdown: If the interpreter has been shut down
"""

def receive(blocking=True, timeout=None) -> Any:
"""Receive an object send to the current interpreter.

Args:
    blocking: Whether this call should block until an object is received
    timeout: Duration of (non-blocking) wait

Returns:
    Any: the next object in the queue

Raises:
    Empty: if the queue is empty
    Shutdown: If the interpreter has been shut down
"""
```

This functionality will also be exposed at the C ABI level as:

```c
/**
 * Send an object to the target interpreter.
 * 
 * interp: A InterpreterID object
 * o: Any sendable object
 *
 * Returns: 0 if successful, 1 if an error has occured
 */
int
_PyInterpreterState_Send(PyInterpreterState* interp, PyObject* o)

/**
 * Receive an object sent to the specified interpreter.
 * 
 * New reference returned
 * 
 * interp: An InterpreterID object. Its GIL must be acquired.
 * blocking: Whether to block execution until an object is received
 * timeout: Duration of (non-blocking) wait
 * 
 * Returns: object if successful, NULL if there was an error
 */
PyObject*
_PyInterpreterState_Receive(PyInterpreterState* interp, bool blocking, long long timeout)
```

## Implementation details

Each interpreter will now have a *message queue* as part of the 
`PyInterpreterState` object. It is created when the interpeter is created,
and deallocated when the interpreter is finalised.  It will be implemented as
a multi-producer, single consumer concurrent queue. In this initial
version of the system, only immutable objects (*i.e.*, objects for which
`isimmutable` returns `True`) will be sendable. `send` will have the
following logic:

```
function Send(interp, o)
    AssertType(interp, InterpeterId)
    AssertTrue(isimmutable(o))

    interp_state <- InterpreterLookup(interp)

    if InvalidRef(interp_state) then 
        error

    IncRef(o)
    if Enqueue(interp_state, o) then
        DecRef(o)
        return res

    return None
```

`receive` will have the following logic:

```
function Receive(interp, blocking, timeout)
    AssertType(interp, InterpreterId)

    interp_state <- InterpreterLookup(interp)

    if InvalidRef(interp_state) then
        error

    Assert(IsGILHeld(interp_state))

    if not blocking then
        o <- TryDequeue(interp_state)
    
    if o is not None or not blocking:
        return o

    ReleaseGIL(interp_state)
    o <- WaitDequeue(interp_state, timeout)
    AcquireGIL(interp_state)
    return o
```

The majority of new code will be the queue implementation. It can be done
such that it is additive and non-invasive, though it will require
cross-platform, native mutex and condition variable functionality. Existing
Python threading primitives cannot be used since the locks need to function
across interpreters.