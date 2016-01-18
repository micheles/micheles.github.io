---
layout: post
title: Half-million sites
---

The largest computation we ever performed in GEM in terms of sheer
number of sites, is a computation for South America with 481,401
sites.  This is actually a small computation compared to SHARE,
because if has a trivial logic tree with a single realization, so it
can be ran in a decent amount of time and it is a perfect test bed
example to understand the features of the tiling in absence of the
logic tree complications.

I will run an analysis by using the latest calculators, which are not
in master yet. The newest calculators have some additional features
that makes a lot of difference in this calculation. In particular,
it is possible to turn off the filtering.

The problem of filtering is that in this case there are so many sites
that the filtering time is very significant: since the source filtering
is done in the controller node, what happens is that all the time is
spent there, whereas the workers just wait for the filtered sources to arrive.
This is an exceptional situation; normally, even with 100,000 sites, the
filtering is fast enough that it makes sense to do it in the controller
node, to save a lot of time in data transfer. Even if there are a lot
of sites, but the source model is relatively small (for instance
when there are few area sources) it makes sense to filter up front.

Actually the sources are filtered twice: up front on the controller
node and then again on the workers. This is not a waste, it is actually
a key idea that improves the performance a lot in all situations except
the most rare. The up front filtering has a few substantial advantages:

1. it reduces the data transfer: only the relevant sources are sent
2. it reduces the filtering on the workers, since only the prefiltered
sources arrives and are refiltered, not all of them
2. it improves the task distribution: without up-front filtering, a source
that theoretically is heavy, could be filtered away in the workers
and actually contribute next to nothing to the running time, thus
tasks that in theory should be heavy could be light.

Point 2 is particularly important, because with a bad task
distribution your computation will be waiting for the slow tasks and
wasting time. So up-front filtering is usually good, but here we are in
a very special situation: the up-front filtering is so slow that it is
worse that the disadvanges. To cope with this situation the new
calculators have a `filter_sources` flag that can be set to `False` to
disable filtering. Since the sources are no more filtered in the
controller node you have to send all of them, but you save time anyway, since
the filtering time is larger than the data transfer time. Also,
waiting for the slow tasks is less inefficient than doing the up-front
filtering.


Single tile
-----------

Before running the tiling calculator, for sake of comparison I run a test
with a single tile. Then the computation is expected to be a lot slower
since the tile is so big. Indeed, with 2,000 tasks
it takes 14 hours and 27 minutes and the data transfer is huge, over
100 GB, at the limits of rabbitmq:

operation          | cumulative time
-------------------|-------------------
computing poes	   | 11,138,363 s
making contexts	   | 1,608,340 s
agg_curves         | 404 s
managing curves    | 132 s
combine/save curves| 12 s
total run time     | 867 m

number of tasks: 2016
data transfer: 21.78 GB sent, 137.39 GB received

The reason for the huge data transfer from the controller node to the
workers is that the site collection is large (11 MB) and we are transferring
it 2016 times. This is dominating factor, since the sources are small in
size compared to a site collection with half million sites. When tiling
is enabled the opposite is true, since the site collection is split and
so a lot less data in transferred there, whereas the sources are send
multiple times and then the sources are the objects dominating the
data transfer.

For what concerns the data transfer from the workers back to the controller
node, this is a case with 481,401 sites, 19 levels and 8 bytes for each
float returned, so each task returns 69.8 MB of data. Multiplied by 2016
we get the huge figure quoted before. With tiling we can reduce this
number by N times, where N is the number of tiles.

Tiles with 20,000 sites
------------------------

My second attempt was to run the same computation split in 25 tiles
and 1100 tasks:

operation          | cumulative time
-------------------|-------------------
computing poes	   | 324,242 s
making contexts	   | 249,334 s
managing curves    | 376 s
agg_curves         | 217 s
combine/save curves| 14 s
total run time     | 86 m

number of tasks: 1100
data transfer: 2.28 GB sent, 3.01 GB received

As you see the results are impressively better. The ratio 
`computing poes/making contexts` is down to 1.3, which is a
decent value, but still larger than 1. It probably means that
we can improve the figures by increasing the number of tiles.
The smaller the tile, the smaller the `computing poes` because
until the computation is dominated by `making contexts` and it
does not make sense anymore to reduce the tiles.

It should be noticed that the time needed to save the curves
it totally insignificant (14 seconds) because we are using the
HDF5 datastore. The time to aggregate the curves (217 seconds)
is fairly small, half than before because we are aggregating
smaller arrays.

The data transfer is 10 times less than before in the controller->workers
direction and 46 times smaller in the workers->controller direction. This
is expected since there are 25 tiles (i.e. 25 times smaller arrays) and
the number of tasks is nearly half as before.

Tiles with 5,000 sites
------------------------

Then I tried to increase the number of tiles to 97, with 1337 tasks,
to see if we could improve the figures again:

operation          | cumulative time
-------------------|-------------------
computing poes	   | 260,652 s
making contexts	   | 284,608 s
managing curves    | 1,337 s
agg_curves         | 258 s
combine/save curves| 14 s
total run time     | 72 m

number of tasks: 1358
data transfer: 7.18 GB sent, 0.98 GB received

The ratio `computing poes/making contexts` is now down to 0.92 and the
data transfer back is three times smaller than before (because the tiles
are smaller). Unfortunately, the data transfer to the workers is over three
times larger, since there are many tiles. To time spent in `managing curves`
is of 22 minutes over a total of 72 minutes: it is clear that we cannot
increase the number of tiles more, otherwise that operation will start
dominating the computation. It would probabily be better to reduce
the number of tiles and/or tasks, since it seems that we are already
seeing the effects of excessive tiling (`making contexts` is below 1
and `managing curves` is significant).

As an exercise, I also tried to run the computation with tiles of 1000 sites,
i.e. with 481 tiles, but it was disaster: the engine ran for several
hours and then rabbitmq died for excessive data transfer, consuming
over 35 GB of RAM and disk space in the mnesia directory.
