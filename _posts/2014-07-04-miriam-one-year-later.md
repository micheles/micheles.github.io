---
layout: post
title: Miriam's island, one year later
---

One year ago I documented the performance improvements of OpenQuake 1.0
for event based calculations, by taking as example a toy model, the so-called
[Miriam's island](/2013/06/12/the-story-of-Miriam-island-2/).

One year has passed, and the release of OpenQuake 2.0 is coming closer:
it is the time to make the point of the situation, and to see which
kind of improvements we can expect for that kind of computation.
In this post I will talk only about the hazard part, by leaving a discussion
of the risk part to the future.

While Miriam's island is a toy model, it shares the performance characteristic
of real life event based computations, and in particular their
shortcomings: so it is a pretty interesting use case. One year ago we
could run the computation in 7 minutes; nowadays the runtime is of
3m40s, i.e. nearly half as before. The improvement was mostly on
the conversion from ground motion fields to hazard curves: before
it was taking half of the time, now it is basically instantaneous
since it is done in memory, without performing any query on the
database.

Here are some numbers for the current master, whereas I have set
the parameter `concurrent_tasks` to 512, so that 539 tasks are generated:

operation   | cumulative time
------------|-----------------
saving gmfs |	27,549 s
computing gmfs | 2,650 s
hazard curves from gmfs | 522 s
saving ruptures | 301 s
generating ruptures | 185 s

As you see the most expensive operation is the saving into the
database, which is 10 times more expensive than the computation of the
ground motion fields. This is [hardly surprising]
(/2014/06/15/the-numbers-for-japan/). We always had this
problem, and the table structure for the ground motion fields is the
same as it was one year ago. We improved enormously on the `hazard
curves from gmfs` operation: now it is done in just 522 cumulative
seconds (i.e. ~1 second per task) whereas until one week ago it took
~50,000 cumulative seconds.  We also improvement on the rupture
generation and saving times: however they were not relevant event
before, so their effect on the total runtime is negligible.

The memory consumption in the tasks is negligible, the maximum allocation
per task is of 55 MB; also in the master the memory consumption is negligible,
the maximum allocation is in the rupture-collecting phase in post_execute
and it takes only 98 MB, even if there are 229,169 ruptures, i.e. a lot.
We improved on the past, but even then the memory allocation was
minor.

The summary for the event based calculator (hazard) is the following:

1. the convertion gmfs -> hazard_curves is now cheap;
2. the saving on the database is still an issue.

Is it possible to do something about 2? Can the refactoring of the table
structure that I [advocated in the past](/2014/06/15/the-numbers-for-japan/)
fill the one order of magnitude gap between saving time and computation time?

For several months I have hoped that it would be the case, based on faith
and some experiments I have performed on my development machine. Today
I have some numbers. I did put the experimental branch with the new
table structure on our cluster and here are the numbers for exactly
the same computation:

operation   | cumulative time
------------|-----------------
saving gmfs |	2,144 s
computing gmfs | 2,710 s
hazard curves from gmfs | 606 s
saving ruptures | 294 s
generating ruptures | 182 s

*It works!* With the new table structure I could improve the saving
time by more than an order of magnitude, by passing from 27,549s to 2,144s,
i.e. with a speedup of 13x! Actually the improvement was better than
my optmistic estimates. The database is much more compact and the
disk space occupation passed from 5860 MB to 3716 MB, i.e. 37% of
the disk space was saved.

The improvement is not restricted to Miriam'island. I repeated the analysis
for Japan, which is a real model, and I got the following numbers:

operation | before | after
----------|----------------
saving gmfs | 310,857 | 101,160
computing gmfs | 32,008 | 24,427
saving ruptures | 7,056 | 4,174
generating ruptures | 2,686 | 2,202

The improvement on the saving time is not of 13 times, but still is
very significant (more than 3x); the other times are better too, since
now the machines are less loaded and they do not need to wait for
free core. It helps that the number of tasks is 515, when befoe it was 701:
with less tasks there is less context switching and the computation is
more efficient.
We saved a lot of memory (1/3 on the workers) and of disk space (35% less):

measured_value | before |after
---------------|--------|------
number_of_tasks| 701 | 515
max_memory_per_core | 1,622 MB | 507 MB
disk_space | 55 G | 36 G
total_runtime| 39m 40s | 32m 7s

The largest memory occupation is in the post_execute phase, whereas 10,010 MB
are used in the controller node. This is a lot, because it is a computation
with a lot of points (42,921) and a lot of ruptures (661,323).

If we want to improve on that computation we need to improve on the
generation of the ruptures phase, which takes 15 minutes, versus
the 16 minutes of the GMF-generation phase. It is hard to improve more
on the GMF-generation phase: even with the new table structure the
saving time is four times bigger than the computation time. Probably
the solution there is to avoid saving the GMFs and to recompute them
on the fly when they are needed, since the computation is so fast
(mind, I am consider the case without spatial correlation in this analysis).
