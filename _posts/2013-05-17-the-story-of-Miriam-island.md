---
layout: post
title: The story of Miriam's Island
---

Once upon a time there was a little island in the Caribbean sea.
It shall be named Miriam's island. Alas, that was not a happy island,
because it was in one of the most seismic regions of the world,
with earthquakes shaking the ground several times per year.
Somebody had the idea of building a virtual city on it, with a little
bit less than 6,000 buildings, and asked us, GEM, to perform a risk
analysis on those assets.

And so our nightmare began. We had just installed our shiny new cluster,
with 256 cores distributed in four workers and 32 cores in a powerful
master, all machines with 128GB of RAM and some terabyte
of disk space. We said: let us test our cluster with this toy
computation, surely it will be a snap for it, a warming exercise
before we start the serious jobs. We launched the computation on a Friday.

On the following Monday, we found the cluster on its knees, swapping like
a mad, with a memory occupation well over the limits.  We
killed everything, and we started a much smaller computation which we
were able to finish. From that we measured the memory consumption and we
estimated that, in order to run the original computation, we would have
needed several terabytes of RAM. But why so? After some lenghty and
painful analysis (which involved writing tools to monitor the memory
allocation of specific blocks of code during the runtime on the
cluster), we discovered that the problem was due to a bug in PostGIS:
there was a GROUP BY involving a GEOGRAPHY field which was allocating
all the memory (and returning bogus results on top of it!).

At that point it was relatively easy to solve the problem, by simply
casting the GEOGRAPHY field to a GEOMETRY field. Now the GROUP BY was
working correctly and the Postgres memory occupation dropped down
drastically. Still the query was so heavy that we could not perform it
hundreds of times on the workers, so we had to change our
strategy. Instead of performing the aggregation on the workers, we did
it once for all in the hazard calculator and we stored the result in
an intermediate table, in a predigested format for the risk. That
meant:

1. doubling the disk space occupation
2. making the hazard calculator much slower

Still, with that cure we had hopes to be able to perform the
original calculation. It turns out these were false hopes.

When we tried again to run the original computation (actually a
slimmer version of it, with a single logic tree realization instead of
ten) on the cluster, we could not: there was still a memory problem,
not as big as before, but still such that all the workers were
swapping, by exceeding the 128 GB limit. This time the problem was not
in Postgres - the master node ran just fine - but in Python: it could not
store in memory the data coming from the database.

To figure out what the problem was, we had to profile in detail
the memory allocation in the Python code and we discovered that
a lot more memory than expected was needed. In particular, to
retrieve a million floats from the database, one would expect
a memory occupation of 8 megabytes (8 bytes per float): instead
something like 40 megabytes were needed. The reason is that a
Python float requires 24 bytes each and the postgres driver was likely
to allocate some additional memory to unmarshall the original data
into Python numbers. So a lot of memory was really needed; on top
of that, we suspected a memory leak, because the memory was not
deallocated at the end of the task, and the only way to free
memory was to kill the celery process pool.

Fortunately we discovered a celery configuration parameter to activate
automatic refresh of the celery processes, `maxtasksperchild`: by
setting that parameter to 1 we made sure that each process could only
run a single task before being killed and restarted.  In this way we
circumvented the suspect memory leak, but we could not run the
computation anyway, because the memory occupation was still too large.

We started then an inspection of the code and a refactoring aimed at
saving memory, for instance by not using intermediate dictionaries, by
using numpy arrays instead of lists, etc. A lot of work, but the minor
memory benefits that we gained were still not enough to run the
computation. Then we discovered that we were returning the same
rupture ids for all assets: since each location had 230,000 rupture
ids, there was a large amount of integers to transfer. They were
actually using the same memory as their companion floats describing
the ground motion values. By returning the ruptures only once and not
6,000 times (I remind the reader that 6,000 is the number of assets),
we were able to nearly cut in half the memory occupation.

But it was yet not enough to run the computation on the full cluster:
with 256 cores running the memory occupation was still too high.
We worked around the problem by increasing the `block_size` parameter,
thus generating less tasks: with 60 tasks we could barely
finish the computation, by remaining a little bit below the 128 GB
limit. But it was not a satisfactory result: our measurements showed
that the larger the number of tasks, the larger the load on the
database: all the time was spent in waiting for the data to be
ready. Moreover we saturated our Gigabit connection: there was
simply too much data to transfer. Doing the computation on a single
machine would have been more efficient than doing it on a cluster,
since the database was the bottleneck.

Experiments done with one tenth of the original computation with
around 300 tasks showed that the total time spent in getting the data
was several times bigger than the time spent in performing the
computation (something like 75,000 seconds vs 3,000 seconds) whereas
a single worker process could allocate up to 4 GB of memory: and
that for one tenth of the original computation!

At this point the situation was good, because we had understood where
the problem was: we were transferring and unmarshalling too much data,
therefore we had to look at ways to reduce the data transfer. In order
to do so, we had a look at our exposure and we discovered that it was
clusterized, i.e. we had groups of geographically
close assets. Clearly if ten assets are close to the same ground motion field,
we can transfer that ground motion field only once, not ten times. That
observation made a gigantic difference: with that optimization for the
first time we were able to run the computation on the cluster, by
using all of the cores, by fitting in RAM and without being dominated
by the database.  This is a story with a happy ending, and here are
the numbers of one of our latest runs:


Parameter              | Value
-----------------------|------
Number of hazard sites | 1792
Average number of ruptures per site | 229,030
Estimated disk space on db | 6,262 MB
Number of assets | 5,689
Number of tasks | 290
Computation cumulative time | 28,011 s
Getting data cumulative time | 23,573 s
Post processing time | 88 s
Maximum memory allocated by a single task | 348 MB
Maximum memory used on a worker | 19.6 GB
Running time | 7m2s

Yes, you have read correctly, the computation that brought our cluster to its
knees now was performed in 7 minutes! And it was taking only 15% of the
available memory!

The problem was solved and Miriam went on vacation...


## Appendix: Miriam's island in Japan

The case of Miriam's island was rather special, in the sense that we
had the hazard computed on a grid of 100 meters. In regular cases,
the hazard is computed on a grid of 5-10 kilometers: that means
that a lot of assets can be associated with a single ground
motion field, since in five kilometers you can have a lot of buildings
and the association is always with the closest ground motion field
available. In regular cases therefore our optimization works
even better: to test that expectation, we moved Miriam's island
in the center of Tokyo, since we had the hazard computed in that
region available. Here are the numbers we got:

Parameter              | Value
-----------------------|------
Number of hazard sites | 1431
Average number of ruptures per site | 203,462
Estimated disk space on db | 4442
Number of assets | 5,689
Number of tasks | 290
Computation cumulative time | 29,470 s
Getting data cumulative time | 1,484 s
Post processing time | 230
Maximum memory allocated by a single task | 86 MB
Maximum memory used on a worker | 12.1 GB
Running time | 9m31s


Here is the story the numbers are telling us: the hazard in Miriam's
island was realistic in terms of ruptures, ~200,000 ruptures per site
are possible in seismic region in the time scale we are considering
(25,000 years). On the other hand, the density of points was not
realistic; where there are less points, more assets share the same
ground motion field and therefore less data is transferred: this
explains why the time to get the data is 20 times smaller than the
computation time. Therefore the computation in Japan is sane, it is
not dominated by the database, and it will scale well if we add more core
to the cluster in the future.

In short, the performance problem in the risk is now solved. We have
now a performance problem in the hazard side, in the post-processing
phase, but that's a story for [another day]
(/2013/06/12/the-story-of-Miriam-island-2.md)...
