---
layout: post
title: The Numbers For Japan
---

For future reference, I report here the number for one of the largest
Event Based calculation we have, i.e. the Japan model with
200 Stochastic Event Set and investigation time of 50 years,
for a total return period of 10,000 years. I am considering here
the case without correlation, which is the one where the issue
of the saving time of the ground motion fields is spectacularly
evident. I have chosen the configuration parameters to generate
701 tasks, which is a good choice for our cluster with 256 cores.

Here are some infos about the source model used, which has 3 tectonic region
types:

tectonic_region_type | 	num_sources | num_ruptures | gsim
---------------------|--------------|--------------|-------
Subduction IntraSlab | 	9250 | 152887 | ZhaoEtAl2006SSlab
Subduction Interface |  8024 | 432570 | ZhaoEtAl2006SInter
Active Shallow Crust | 11571 |  75866 | ZhaoEtAl2006Asc

As you see most of the ruptures (432,570) comes from the *Subduction Interface*
region, and the total number of ruptures generated in the return period of
10,000 years is 661,323.

The total runtime of the full computation is a bit less of 40 minutes,
which is quite impressive given the size of the computation.
Still, the runtime is totally dominated by the *saving gmfs* procedure,
which takes nearly 10 times more time than the *computing gmfs* procedure.
The situation is similar for the ruptures: the saving time is nearly
3 times bigger than the computing time. However in this computation
this is not an issue because the rupture generation time is dwarfed
by the ground motion field generation time. That because we are
considering ~40,000 sites. In site-specific analysis, on the contrary,
the rupture generation part is the dominant factor, since for few
sites the ground motion field generation takes a negligible amount
of time.

The computation wrote 55 GB of data, obtained by measuring the
full size of the database before and the full size after. That assumes
that no other procedures were writing or purging the database in the
meanwhile. The storage is quite efficient; 9,726,005 rows where written
in the table gmf_data, with arrays of average length of 430: that
means that the saving procedure is as fast as possible with the
current database structure. We had much worse performance in the
past, in cases when we where saving short arrays.

You can see all the numbers in the table below:

operation | cumulative time
----------|----------------
saving gmfs | 310,857 s
computing gmfs | 32,008 s
saving ruptures | 7,056 s
generating ruptures | 2,686 s

All other operations are fast and I am not reporting them here
(the slowest among the other operations is *filtering ruptures*,
with 1,325 cumulative seconds, not much). I will instead notice
that this computation requires a lot of memory for the *computing gmfs*
operation:

operation | max_memory_per_core
---------------|-------------
computing gmfs | 1,622 MB

This is due to the fact that the calculator has to collect in memory
the generated ground motion fields, for the purpose of storing them
in the database efficiently. If we changed the database structure
we could avoid that and save memory. Still, this is not an issue
for us at the moment. During this computation the peak memory
occupation on the workers was of 50 GB, but we have 128 GB
available, so we can still scale. Since we have 64 core per
worker, the average memory per core was around 800 MB, i.e. half
of the maximum memory per core of 1622 MB.

During of the computation most of the cores did not work: they were
just waiting for the ground motion fields to be saved. If you could
reduce the saving time by an order of magnitude, say from ~300,000
seconds to ~30,000 seconds, by making it comparable to the generation
time, then we could reduce significantly the total runtime.

Notice that 310,857 cumulative seconds divided 256 means that each
core spent in average 20 minutes to save the ground motion fields.
If we can reduce that time to 2 minutes we can save 18 minutes
from the total runtime, i.e. more or less half of the time.

We will see at the end of this sprint if the refactoring of the
database that I am performing will be able to achieve that goal.
Of course, the difficult thing is not to improve the hazard
calculator, the difficult thing is *to not deteriorate the performance
of the risk calculator*. At the moment the risk calculator explodes
with the refactoring that I have already done with a hard out-of-memory
issue: but I am an optimist. These things never work at the first attempt.
The secret is to keep trying.

PS: the astute reader will notice that the numbers do not add up: I
said that the dominant factor was the saving time, but even if I
reduce that to zero, I wrote that I hope to reduce the total computation time
only of a half: then, where is spent the other half of the time?

Some of the time is spent in reading the source model and
storing the sites, but that is fast, under one minute.
A lot of the time is spent in data transfer, first
sending the sources to the workers so that the ruptures
can be computed (700 MB of data are transferred).
When the ruptures have been computed, they are sent back
to the controller node, that sends them again to the workers
(this round trip is necessary since without it it
would extremely difficul to produce homogeneous tasks).
That takes some time, since ~2900 MB of data must be
transferred. The phase where the ruptures are computed
takes more or less 8 minutes in total. The phase where
the ground motion fields are computed takes 31 minutes.
One must also take in account that not all tasks are
equal and that the system has to wait for the slowest task.
