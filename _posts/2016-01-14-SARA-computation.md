---
layout: post
title: The SARA calculation: before and after
---

In this post I will document the performance improvements of the
classical tiling calculator in a real life calculation, i.e. a
computation for the SARA (South America Risk Assessment) project.
This is a computation with 50,796 sites and a logic tree with 12
realizations.

It is a large computation. When we ran it before Christmas with the
old tiling calculator it took 1 day, 10 hours and 43 minutes to run,
i.e. 2083 minutes. The most expensive computation was computing the
probabilities of exceedance, with over 11 million of cumulative seconds:

computing poes: 11,041,287 s

For comparison, the time spent in making contexts was 27 times smaller:

making contexts: 401,699 s

The computation had only 2 tiles, but this is case where we could not
generate many tiles, otherwise the time needed to manage the source
model would have killed the performance. Already with 2 tiles we spent
over 11,000 sequential seconds just to read, filter, split and send
the sources, i.e. over 3 hours.

initialize sources: 11,303 s

In this calculation the parameter `concurrent_tasks` was not touched,
so the default of 256 was used and with two tiles 484 tasks were
generated.

With the new tiling calculator the figures changed as follows:

concurrent_tasks: 4,295

number of tiles: 51

computing poes: 9,077,264 s

making contexts: 474,483 s

managing the sources: 2,377 s

reading composite source model: 350 s

As you see, `making contexts` takes a bit more time than before: the reason
is that now there are a lot more tasks, 4,295 instead of 484. Having more
tasks makes the total computation time a little bigger, but has the advantage
of improving the task distribution, so the total runtime of the computation
can actually be (much) better. `computing poes` should be a bit bigger than
before, since there are more tasks,  but actually is a bit less:
the reason is now we have a lot of small tiles (51) and it is more
efficient to compute the PoEs with shorter arrays. This is the reason
why the ratio computing poes / making contexts is decreasing:

ratio computing poes / making contexts = 19 (it was 27)

Also, we are saving a lot of time in `initialize sources` since the
new calculator does not need to read again the same source model once
per tile, it reads it just once (in 350 s). There is still time spent in
the operation `managing the sources` that includes filtering,
splitting and sending the sources to the workers (2,377 s).

From such figures, it does not look like the new calculator it is much
better from the old one: but the reality is that it is a lot better,
since the task distribution is a very uniform. So the total runtime
went down from 2083 minutes to 762 minutes, a speedup of nearly three times:

Total speedup factor: 2.7x

Before, most of the time was spent waiting, now it is not the case anymore.
If you consider that 10 million of cumulative seconds split in 256 cores
means that every core run in average for 11 hours, whereas the run time
of the computation was a bit over 12 hours, it means that *we
are near to the optimum*, considering that some time must be
spent in initialization and post processing. We cannot improved much
for what concerns the tasks distribution, now we can only improve by optimizing
hazardlib.

The computation is large and involve a lot of data transfer, but nothing
that our cluster could not manage: 5.5 GB were sent and 12.83 GB were
received.

The time needed to aggregate the curves is larger in the new
calculation simply because there are more tasks (2094 s instead of 594
s) but it small enough to be ignored. It is always possible to reduce
the number of tasks by decreasing the parameter `concurrent_tasks`.

The time needed to combine the curves and to compute the statistics
is negligible (a couple of minutes) because the logic tree is small.
The time to save the hazard curves is also insignificant, whereas
in the old computation it was around 25 minutes. The improvement
here is related to having removed the database.
