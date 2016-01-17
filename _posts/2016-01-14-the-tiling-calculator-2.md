---
layout: post
title: The oq-lite tiling calculator
---

As we discussed in [the previous installment]
(/2016/01/14/the-tiling-calculator-1/), the current tiling calculator
is not without its shortcomings. For one, the total runtime is very
dependent on the number of tiles generated. Moreover, even if you get
the number of tiles right the load distribution during the calculation
is very discontinuous: when a tile is near to its conclusion or just
at the beginning the workers do not work at all.  If we look at the
graph of the CPU usage on the workers, it is a series of bumps, one
bump for each tile. Therefore if you produce too many tiles you will
have lots of bumps and lots of time spent idly reading the source
model, filtering and sending the sources, things that are repeated for
each tile. The number of tiles produced is determined by the parameter
`maximum_tile_weight` which must be passed by the user, and it is
tricky to get a good value for it.

All such problems have been known
from the beginning.  The reasons why they are are here is that the
tiling calculator was implemented it in a hurry, because there was a
deadline on a calculation that could not be done without tiling, so we
spent something like 3 days on it when a decent solution would have
required at least 3 weeks of work.

Since then I spent a long time thinking on a parallel tiling calculator
and at the moment I am writing (half of January 2016) the engine code base
has a parallel tiling calculator that can be accessed with the
``--lite`` flag. When you give this flag, instead of old sequential
tile calculator, you can run a parallel calculator based on
the HDF5 datastore. Actually there is a difference between the lite
calculator in release 1.7 and in the current master: the newest one
splits the heavy sources and parallelizes much better. It is the
one that I will consider in the analysis below.

It is important to point out that all calculators use the same
library (i.e. hazardlib) i.e. their performance is theoretically
the same in terms of sheer calculation. In practice, however,
the oq-lite tiling calculator is more performant for three reasons,
in order of relevance:

1. computing the PoEs with a lot of small arrays is more efficient than
with big arrays (even 10+ times more efficient!)
2. the new calculator does not need to reprocess fully the source model
for each tile, it just filters and send the sources
3. the new calculator does not have idle time between on
tile and the other
4. the oq-lite calculator writes in the HDF5 datastore,
which is much more efficient than the database.

Using a single tile
----------------------------------------

Even in absence of tiling, the oq-lite classical calculator is a bit
better than the engine calculator, so for the SHARE computation
discussed in the previous installment the total runtime goes down to
14 hours instead of 18.5 hours. We are actually saving 4+ hours for
not saving in the database, plus other small improvements. However it
is not much. Since there is a lot of data to save (12+ GB of hazard
curves) so you save some hours. However, the other times are not much
different than before:

operation          | cumulative time
-------------------|-------------------
computing poes	   | 5,164,142 s
making contexts	   | 169,687 s
combine/save curves| 6,001 s
compute/save stats | 834 s
agg_curves         | 33 s
total run time     | 836 m

number of tasks: 463

The difference is in `making contexts` is more apparent than real,
since the oq-lite calculator measure less operations than the engine
calculator for this operation (technically it does not measure
the time spent in .iter_ruptures).

The message to bring home is that
*unless you have a lot of data to save you should not expect
significant improvements with respect to the time-honored engine
calculator*.

Using 50 tiles
-------------------------

The situation is different for the tiling calculator. Here one expects
some definite improvement. Let's see how the calculation goes by
default, i.e. without tuning the number of tiles. By default the
oq-lite tiling calculator produces tiles with 1,000 sites, therefore
in this case (50,000 sites) it will produce 50 tiles.
There is a parameter `sites_per_tile` that you can
tune if you want to produce larger or smaller tiles. `sites_per_tile`
is certainly much easier to explain and to understand that the
`maximum_tile_weight` parameter of the sequential calculator.
Here are the figures for the classical_tiling calculator:

operation          | cumulative time
-------------------|-------------------
computing poes	   | 186,213 s
making contexts	   | 81,280 s
combine/save curves| 6,479 s
compute/save stats | 884 s
agg_curves         | 199 s
total run time     | 219 m

number of tasks: 2,250

As you see, there is an enormous improvements for `computing poes` (as
speedup of ~28 times) and a significant speedup for `making contexts`
(2.1 x). The other operations are compatible with the non-tiled ones
and not relevant. Still there are no miracles, and the runtime of
`computing poes` and `making contexts` are compatible with the engine
tiling calculator with 17 tiles. The advantage is in the task
distribution, which is better, and in the saving times. That explains
while the total runtime is 219 m, to be compared with the 255 m of the
old calculator. Still, it is not a revolutionary improvement.

The important point to notice here is that *with the default parameters
the oq-lite calculator is competitive (and usually better) than
then old engine tiling calculator with a careful tuning*.

Using 500 tiles
-------------------------

To stress the calculator, I ran it with
tiles of 100 sites, thus producing 500 tiles, a lot.
In this case a significant amount of time is spent sending the sources,
because the same sources are send to the workers multiple
times (up to 500 times for a source which affects all tiles).
The total runtime nearly double and the computation takes
nearly 7 hours to run.

operation          | cumulative time
-------------------|-------------------
computing poes	   | 509,587 s
making contexts	   | 367,662 s
combine/save curves| 6,167 s
filtering sources  | 1,077 s
compute/save stats | 802 s
agg_curves         | 270 s
total run time     | 402 m

number of tasks: 4,500

As you see, everything has become inefficient. There are too many small
tasks, and over 50 GB of data have to be transferred to the workers.
Having so many tiles is definitively a bad idea. Still, the oq-lite
calculator is much better than the engine one, because with that one
we would have spent ~20 hours just in processing the source model for
500 times!
