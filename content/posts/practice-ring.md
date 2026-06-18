+++
title = 'Practicing Programming #1: Ring Queue in C'
description = 'Notes on trying to implement different things and learning to be intentional and efficient.'
date = '2026-06-15T21:10:10+04:00'
+++

I must admit I'm pretty bad at programming. I have a habit of wasting a lot of time and jumping straight into
code before doing any design.

In this series of short posts I'd like to work on my shortcomings by making tiny projects while focusing on
being more intentional, precise and efficient.

---

One thing I had a struggle with recently was ring queue. It's purpose was to allow me to not use callbacks
for window messages in a small game library I was writing at the time. I wanted it to be a C "template" type:

```c
#define ring_t(_T) struct { _T *data; size_t n, m, tail; }
#define ring_push(_r, _v) /* ... */
#define ring_get(_r) ((_r).data[(_r).tail])
#define ring_pop(_r) do { \
        assert((_r).size); \
        (_r).tail = ((_r).tail + 1) % (_r).allocated; \
        (_r).size--; \
    } while (0)

ring_t(int) ints;
int one = ring_get(ints);
ring_pop(ints);
```

I wanted it to be pretty simple and able to work inside fixed memory block as well as the heap.

The template format fits the first condition pretty well and the second can be satisfied by adding
`push_noalloc()`. Also there wasn't a need for adding or removing more than one element at a time or for it to be thread-safe.

This is the complete interface:
```c
#define ring_t(_T) struct { _T *data; size_t size, allocated, tail; }
#define ring_init(_r)
#define ring_push(_r, _v)
#define ring_push_noalloc(_r, _v)
#define ring_peek(_r)
#define ring_pop(_r)
#define ring_free(_r)
```

Pushing an element to the queue means doing the following:
- expanding the underlying buffer if `size + 1 > allocated`
  - expanding `data` to `(allocated << 1) + 1`
  - moving `data[tail:allocated - tail]` to the end of the block and updating `tail` if `tail + size > allocated`
  - updating `allocated`
- updating `data[(tail + size) % allocated]` element
- incrementing `size`

This is what I ended up with:
```c
#ifndef RING_REALLOC
    #include <stdlib.h>
    #define _RING_STDLIB_INCLUDED
    #define RING_REALLOC(_p, _s) realloc((_p), (_s))
#endif

#ifndef RING_FREE
    #ifndef _RING_STDLIB_INCLUDED
        #include <stdlib.h>
    #endif
    #define RING_FREE(_p) free(_p)
#endif

#ifndef RING_MEMMOVE
    #include <string.h>
    #define RING_MEMMOVE(_dst, _src, _s) memmove((_dst), (_src), (_s))
#endif

#define ring_t(_T) struct { _T *data; size_t allocated, size, tail; }
#define ring_init(_r) do { (_r).data = 0; (_r).allocated = (_r).size = (_r).tail = 0; } while (0)
#define ring_peek(_r) ((_r).data[(_r).tail])
#define ring_pop(_r) do { (_r).size--; (_r).tail = ((_r).tail + 1) % (_r).allocated; } while (0)
#define ring_free(_r) do { RING_FREE((_r).data); ring_init(_r); } while (0)
#define ring_push_noalloc(_r, _v) do { \
        (_r).data[((_r).tail + (_r).size) % (_r).allocated] = (_v); \
        (_r).size++; \
    } while (0);
#define ring_push(_r, _v) do { \
        if ((_r).size + 1 > (_r).allocated) { \
            (_r).data = RING_REALLOC((_r).data, sizeof(*(_r).data) * (((_r).allocated << 1) + 1)); \
            if ((_r).tail + (_r).size > (_r).allocated) { \
                RING_MEMMOVE( \
                    (_r).data + (((_r).allocated << 1) + 1 - ((_r).allocated - (_r).tail)), \
                    (_r).data + (_r).tail, \
                    sizeof(*(_r).data) * ((_r).allocated - (_r).tail) \
                ); \
                (_r).tail = (((_r).allocated << 1) + 1 - ((_r).allocated - (_r).tail)); \
            } \
            (_r).allocated = ((_r).allocated << 1) + 1; \
        } \
        ring_push_noalloc((_r), (_v)); \
    } while (0)
```

At some point I forgot to update `tail` after `memmove` which resulted in `peek()` *sometimes* returning garbage. I spend too much time on this issue when I simply had to write down the algorithm and compare it to what I've already wrote.

So one thing I should certainly take as a lesson is to make a checklist (steps of the algorithm) even if it feels trivial or dumb. Especially when I get stuck on a bug that happens randomly.

And test, always test. Ideally with a reference implementation.