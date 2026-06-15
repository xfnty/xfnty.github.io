+++
title = 'Practicing Programming #1: Ring Queue in C'
description = 'The first post in the series where I practice problem solving and programming in general.'
date = '2026-06-15T21:10:10+04:00'
draft = true
+++

I recently decided to resurrect my blog and start a series where I find relatively challenging
but approachable programming thing, write a spec for it and then do the implementation while
being as focused and efficient as I can.

My goal is to get better at solving problems and reflecting on how I did it.

What made me think about doing this was me being unable to write the most basic ring queue for a window
message pump in one sitting and then not want to tie a rope around my neck while debugging it. Unfortunately
and sadly I failed.

I also noticed that I tend to avoid designing or planning or any thinking-heavy work in general which lead me
to wasting shamefully large amounts of time and energy on projects I eventually abandon. I'd like to break
that cycle.

So I think I'll start small and just keep my pace. Wish me luck)

---

So, the ring queue. It's purpose was to allow me to not use callbacks for window messages in a small game
e̸̠̚n̷͔̆g̶̖̏ǐ̶̲n̷͉͝ḙ̴̉  I was writing at the time. I wanted it to be a C "template" struct in the style of [klib][klib] from
the [Attractive Chaos][ac] github repo.

It was supposed to look like this:

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

By the way this pattern is now supported by C23 standard with [type compatibility][n3037].

[klib]: https://github.com/attractivechaos/klib
[ac]: https://github.com/attractivechaos
[n3037]: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3037.pdf
