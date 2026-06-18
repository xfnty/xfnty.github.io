+++
title = 'Practicing Programming #2: malloc'
description = 'Dipping my toes in the waters of memory allocation.'
date = '2026-06-18'
draft = true
+++

```c
void *malloc(size_t size);
void *realloc(void *ptr, size_t new_size);
void free(void *ptr);
```

Left out alignment, size queries, locking & defragmentation.