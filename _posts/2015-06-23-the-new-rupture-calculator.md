---
layout: post
title: The new rupture calculator
---

In a [previous post](/2015/06/21/the-8-event-based-calculators/) I listed
the event based calculators available in the engine. Here I will discuss
in more detail the calculators #1 and #2, i.e. the old and the new
rupture calculator. Both calculators read the source model and produce
ruptures; they both use the same algorithm; however the old calculator saves the
ruptures on a Postgres database (as pickled Python objects stored in a
text field), whereas the new calculator saves the ruptures directly
on the filesystem (as pickled Python objects).

The old rupture calculator worked usually well, but had a performance
issue when a lot of ruptures were generated. In such a case
storing the ruptures in the database was inefficient. Let me consider
for instance the good old
[Miriam's island](/2013/05/17/the-story-of-Miriam-island/), which is
a computation with a lot of ruptures (228,567 of them,  but there
are much bigger computations). In such case the old calculator gives
the following figures, starting from a database half empty:

Operation              | Cum. Time
-----------------------|-----------
generating ruptures    | 141 s
filtering ruptures     | 78 s
saving ruptures        | 684 s

As you see, the saving time is much bigger than the generating time (~5
times more). The problem is solved by the new calculator. The figures
are:

Operation              | Cum. Time
-----------------------|-----------
total compute_ruptures | 197 s
saving ruptures        | 5 s

Notice that `total compute_ruptures` computes the ruptures and also filters
them, so the 197s of the new calculator should be compared with the
141 + 78 = 219s of the old one. So we acheaved a slight improvement
of the calculation time too; but the selling point of the new calculator
is the spectacular speedup in the saving time, from 684s to 5 s, over
two orders of magnitude!

The speedup can be seen even in other computations. For instance,
we have a computation for Turkey producing 1,494,422 ruptures (!) with a
saving time of 4,439 seconds; with the new calculator the time goes
down to 86 seconds. For comparison, the time to generate and filter
the ruptures goes down from 6,385s to 3,749s.

So, there is a definite improvement, which is particular relevant
for site specific analysis. On the other hand, if your calculation
has a lot of sites and you want to save the ground motion field
on all sites, that part will certainly dominate the computation time.
In other words, it is a lot more important to speed up the saving
time of the GMFs rather than the saving time of the ruptures.
For that, you need [the new GMFs calculator]().
