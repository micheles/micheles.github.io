---
layout: post
title: The classical tiling calculator
---

What should we do if a computation becomes so large in terms of number
of sites, that it runs out of memory and cannot be performed? Of course,
we should try to split it in smaller computations.

This is easy if there is no correlation between the sites, i.e. for
classical PSHA calculations. In that case we can just split the
computation in tiles (blocks of sites) and run one tile at the
time. We implemented such a solution a couple of years ago and since
then we have a `classical_tiling` calculator in the engine.

The calculator was implemented to solve the memory issue, but
then we discovered that it had other benefits as well: in particular
*splitting a computation in tiles can make it a lot faster*.

An example with a single tile
------------------------------

To show what happens in concrete I will consider as an example a
reduced SHARE computation with 50,000 sites and a logic tree of 1280
realizations (the full model has ~130,000 sites and 3200 realizations)
which I ran in our Zurich cluster. Even if reduced, the computation is
still quite large and if you run it without tiling it will take 18 hours
and 33 minutes. Here are the figures with the parameter `concurrent_tasks`
set to 500:

operation         | cumulative time
------------------|-------------------
computing poes	  | 4,976,525 s
making contexts	  | 331,149 s
save_hazard_curves| 20,755 s
post proc         | 2,058 s
initialize_sources|	428 s
agg_curves        | 292 s
total run time    | 1113 m

Some remarks are in order, to highlight the bottlenecks of the computation.

1. The operations `making contexts` and `computing poes` are the core
operations performed in hazardlib. The first one compute several things,
in particular the distances source-sites for all sources, the second
one computes the probabilities of exceedance for all sites and sources.
In this case the `computing poes` time dwarfs the `making contexts` time:
it is 15 times bigger. This is normally the case when you have a large
GMPE logic tree.

2. A lot of time is spent in saving the hazard curves, 20,755 s which
means 5h 46m on a computation of 18h 33m. This problem is not related
to the tiling, but to the database. It is solved in the HDF5-based
calculators, where the saving time of the curves becomes essentially
zero.

3. The time spent in reading the source model (7 minutes) is negligible
and so it the time spent aggregating the curves (5 minutes). The bulk of
the time is spent in the execute phase (12 hours).

Using 4 tiles
--------------------------------------------------

Doing the same identical computation with only 4 tiles of 12,500 sites
each reduces significantly the run time from more than 18 hours to a
bit less than 6 hours: the net speedup is over 3 times! Here are the
numbers:

operation         | cumulative time
------------------|-------------------
computing poes	  | 479,283 s
making contexts	  | 155,036
save_hazard_curves| 11,284
post proc         | 747 s
initialize_sources|	955 s
agg_curves        | 288	s
total run time    | 353 m

The reason for the speedup is the drastic reduction in `computing poes`,
which takes now over 10 times less time than before. On the other hand
`making contexts` takes half the time than before. Same for 
`save_hazard_curves`. There are two reasons for that.

1. The [logic tree reduction effect]
(https://github.com/gem/oq-risklib/blob/master/doc/effective-realizations.rst):
the tiles are such that some tectonic region types are filtered away
and the logic trees becomes much smaller, so a lot less computations
are needed.

2. Even if the logic tree is not reduced, it is a lot fast to compute
the PoEs (that involves a lot of matrix multiplications) by splitting
in small tiles.

Also, it should be noticed that a lot more tasks are generated: 1807
instead of 463. The reason is that with `concurrent_tasks = 500` we
are going to generated around 500 tasks per tile and since there are 4
tiles we are going to generate 4 times more tasks.

The total runtime is very dependent on the number of tiles generated.

Using 17 tiles
----------------------------------------

The following are the figures for a run with 17 tiles of ~3000 sites
each.

operation         | cumulative time
------------------|-------------------
computing poes	  | 199,663 s
making contexts	  | 127,436 s
save_hazard_curves| 8,157 s
post proc         | 407 s
initialize_sources|	2,352 s
agg_curves        | 292	s
total run time    | 255 m

The number of tasks is 7691, around 17 times bigger than with a single tile, as
expected. This is not a problem for the moment, but if we increased again
the number of tiles we will get even more tasks, which means
more data transfer, more effort on celery/rabbitmq, more risk for the
computation to fail and a general slow down.

The operations `making contexts` and `computing poes` are taking still
less time, because of the smaller arrays. They are now so small that
actually the part dominating the computation runtime is saving the
hazard curves, 2h 15m on a computation of 4h 15m. Also, a lot of time
is spent initializing the sources, i.e. reading them from the source
model and filtering them with respect to the current tile: 2,352 s,
which means 39 minutes.

The Zurich cluster has 192 nodes and the total time spent in the tasks
is around 370,000 seconds: so if we has perfect work distribution
the computation should take 370,000 s / 192 = 32 minutes. Instead
the execute phase takes 67 minutes. There is clearly room for
improvement. By optimizing the task distribution we should
be able to double the speed (at maximum).

In general it is best to have few tiles to avoid idle time; however
using too few tiles may produce a slower computation. As you see
things are tricky. You can get huge differences in runtime depending
on a parameter which is difficult to set correctly and in any case a lot
of time is wasted waiting between one tile and the other.

What we would really need is a *parallel tiling calculator*. One that
computes all the tiles in parallel at once, without idle time. Also,
one smart enough to determine automatically a decent number of tiles,
without having the user fiddle with a configuration parameter. I mean,
there should be a parameter to tune the size of a tile, but the
computation runtime should not be too much sensitive to that parameter,
and there should be a sensible default. With the current calculator
there is no default and the user is forced to set `maximum_tile_weight`
manually, usually to a bad value. With the parallel calculator the
user should not set anything and everything should work decently enough
without need of further tuning.

In the last months I have worked a lot on the tiling calculator and now
we actually have two different parallel calculators, that I will discuss
in the next installments.
