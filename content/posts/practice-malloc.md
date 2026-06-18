+++
title = 'Practicing Programming #2: Heap Allocator'
description = 'Dipping my toes in the waters of memory allocation.'
date = '2026-06-18'
draft = true
+++

An allocator for a game.

```c
enum {
    MEMORY_ERROR_HANDLE = -1,
    MEMORY_ERROR_SIZE   = -2,
    MEMORY_ERROR_LOCKED = -3,
    MEMORY_ERROR_NOMEM  = -4
};

typedef int handle_t;

#define MEMORY_HANDLE_OK(_h) ((_h) > 0)

void memory_init(
    void *initial_block, 
    size_t initial_size, 
    void *(*block_realloc)(void*,size_t)
);

handle_t memory_alloc(size_t size, size_t alignment);
handle_t memory_realloc(handle_t h, size_t new_size);
void memory_free(handle_t h);

void *memory_lock(handle_t h);
void memory_unlock(handle_t h);
```

todo: heap walk, defrag to threshold

parts:
- array of pointers to blocks
- multiple blocks of memory each having
  - pool of allocated regions (generation, offset, size, used & locked bits)

Handle should be an index into region pool and a block it belongs to.