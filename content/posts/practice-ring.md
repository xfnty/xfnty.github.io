+++
title = 'Practicing Programming #1: Ring Queue in C'
description = 'Notes on trying to implement different things and learning to be intentional and efficient.'
date = '2026-06-15T21:10:10+04:00'
draft = true
+++

I must admit I'm pretty bad at programming. I have a habit of wasting a lot of time and jumping straight into code before doing any design.

In this series of short posts I'd like to work on my shortcomings by making tiny projects while focusing on being more precise and efficient. 

---

One thing I had a struggle with recently was ring queue. It's purpose was to allow me to not use callbacks for window messages in a small game library I was writing at the time. I wanted it to be a C "template" type:

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

The template format fits the first condition pretty well and the second can be satisfied by having an additional `push_noalloc()` method. Also there is no need for adding or popping more than one element at a time.

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

`ring_init()` zeros out the fields, `free()` and `push()` use `realloc()` and `free()`. `push_no_alloc()` may panic on buffer overflow.