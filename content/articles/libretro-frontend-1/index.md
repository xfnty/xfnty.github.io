---
title: Writing Libretro Frontend From Scratch (Part 1)
description: Requirements and design.
date: Jun 17, 2025
---

A while back I wrote a simple Libretro frontend using SDL which I used to play Armored Core 1 with 
mouse support. It had issues with saving and loading game state, it ran at ~20 FPS when 60 was 
expected (because it used software rendering) and it often crashed due to thread synchronization 
issues. It also didn't have any user interface and so you couldn't change any core settings or 
hotkeys.

For this project I wanted to make a more general purpose frontend with decent user interface, better
support for hardware rendering and plugins, written in Lua.

Also this is the first time for me actually writing down any kind of design document, so it should 
be a good learning oppotrunity.

So, what features do I want?

# MVP or version 1.0

This version is supposed to have the most minimal set of features required to run a Retro core
except also supporting hardware rendering.

Constraints/Requirements:
- Support 64-bit Windows 10 only.
- Use OpenGL 3.3 Core profile for rendering.
- Keep executable small.
- Don't allocate memory during runtime unless it is absolutly necessary.

Features:
- Choosing which Libretro core to use.
- Opening game ROM and beginning emulation immedietly after.
- Choosing save files to create or load.
- Showing emulation frame budget (actual frame time divided by expected time).
- Using OpenGL for hardware rendering or software rendering as a fallback.
- Letterboxing.

Emulator interface:
- Toolbar
  - System
    - Open Libretro core
    - Open game ROM
    - Load state
    - Save state
    - Exit
  - Help
    - GitHub link
    - About
- Viewport
- Status bar
  - Libretro core name
  - Loaded game ROM file name
  - Rendering method
  - FPS
  - Frame budget

This is how it's supposed to look:

![](1.webp)

![](2.webp)

The lifecycle of the app is super simple:

![](3.webp)

# First Steps

I started setting up the project a little earlier without much thought to it. I decided to opt out 
of using CMake this time after reading [an article][article] about not using CRT in Windows apps and
it kind of inspired me a little. I also remembered how I compiled RAD debugger for the first time.
You type `build` and it works. Just like that. No need for multiple `CMakeLists.txt` and presets. I
am not planning to compile this project for anything but Windows anyway and I doubt it would benefit
significantly from incremental builds.

So I spent about 2 to 3 hours trying to make my program compile with `/nodefaultlib` set and make 
`build.bat` print build time and artifact size. Now my ~350 LoC program builds in less than a second
from scratch.

```
----- Compiling "dist" -----
unity.c

Size: 6144 bytes
Time: 0.89 seconds
```

If I didn't include `windows.h` and declared every WinAPI function by hand it would be even faster.
Though it's not like this matters much but still, seeing numbers go up makes my brain tickle.

I thought about using `stb_sprintf` instead of one from standard library but instead I wrote my own 
in about 100 LoC. I didn't think it could be that simple. From this point I'll try to use as few
external libraries as possible.

[article]: https://nullprogram.com/blog/2023/02/15/