+++
title = 'Practicing Programming #1: Ring Queue in C'
description = 'Notes on trying to implement different things and learning to be intentional and efficient.'
date = '2026-06-15T21:10:10+04:00'
draft = true
+++

I must admit I'm pretty bad at programming. I have a habit of wasting a lot of time and jumping straight into
code before doing any design.

In this series of short posts I'd like to work on my shortcomings by making tiny projects while focusing on
being more precise and efficient.

---

One thing I had a struggle with recently was ring queue. It's purpose was to allow me to not use callbacks
for window messages in a small game library I was writing at the time. I wanted it to be a C "template" type:

```c
#define ring_t(_T) struct { _T *data; size_t n, m, tail; }
#define ring_init(_r) do { \
        (_r).data = 0; \
        (_r).n = (_r).n = (_r).tail = 0; \
    } while (0)
#define ring_push(_r, _v) /* ... */
#define ring_get(_r) ((_r).data[(_r).tail])
#define ring_pop(_r) do { \
        assert((_r).size); \
        (_r).tail = ((_r).tail + 1) % (_r).allocated; \
        (_r).size--; \
    } while (0)

ring_t(int) ints;
ring_push(ints, 1);
int one = ring_get(ints);
ring_pop(ints);
```

I needed it to be pretty simple and being able to work inside fixed memory block.

The template format fits the first condition pretty well and the second can be satisfied by having
`push_noalloc()`. Also there is no need for adding or popping more than one element at a time.

This is the complete interface:
```c
#define ring_t(_T) struct { _T *data; size_t size, allocated, tail; }
#define ring_init(_r)
#define ring_push(_r, _v)
#define ring_push_noalloc(_r, _v)
#define ring_get(_r)
#define ring_pop(_r)
#define ring_free(_r)
```

Pushing an element to the queue means doing the following:
- expanding the underlying buffer if necessary
  - reallocating `data`
  - moving `data[tail:allocated - tail]` to the end of the block if `tail + size > allocated`
  - setting `allocated` to `allocated << 1 + 1`
- updating `data[(tail + size) % allocated]` element
- incrementing `size`

This is what I ended up with:
```c
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

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

One thing I should take as a lesson is to write down the algorithm when I get even if it feels trivial or dumb. Especially when I get stuck on a bug that happens randomly.