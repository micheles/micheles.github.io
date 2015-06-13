---
layout: post
title: The Numbers of the Event Based Calculator
---

Event Based calculations are the most challenging calculations we
have in the OpenQuake Engine.
The underlying problem is the sheer size of the generated ground motion
fields. Suppose for instance we want to address a computation
with 100,000 hazard sites, which is typical for a regional
size computation; suppose we need to consider 10 Intensity Measure Types
and 10 Ground Motion Prediction Equations, which are not unrealistic;
finally suppose the number of stochastic event set and the investigation
time are large enough to generate one million of ruptures, which is
actually quite possible in very seismic countries. Then the
number of generated floats would be 

 `num_sites * num_imts * num_gmpes * num_ruptures = 10 ^ 13`

Considering 8 bytes for each float the disk space needed to store the
generated ground motion fields is of 73 terabytes. *Terabytes*. Suppose
that we can store this data at the speed of 10 M/s (which is highly
optimistic, a database has contraints to check when inserting each
row, it is slow by construction), then the writing time is of 93
days. After that, the data has to be read from the risk calculator. Even
assuming a fast reading speed of 100MB/s it would take at least 9
days. But since the data have to be transferred to a remote machine
the bottleneck is the network speed, so that number can be much
longer. And then the computation has to start and write back a lot
of results into the database.

With these numbers everything seems hopeless. Luckily in real computations
the situation is not so terribly bad. So let me give some numbers for a
real use case we have, i.e. the [event based computation for Japan]
(http://2014/06/15/the-numbers-for-japan/),
considering a time span of 10,000 years:

Parameter    | Value
-------------|--------
num_sites    | 42,921
num_imts     | 5
num_gmpes    | 3
num_ruptures | 661,323

According to my analysis the needed space should be

 `num_sites * num_imts * num_gmpes * num_ruptures * 8 bytes = 3.1 TB`

which seems hopeless, given that we have less of 1 TB of disk space
directly available to the database. In reality we are able to finish
the computation because the engine performs an optimization:
*it does not store zeros*. As a matter of fact, most of the ground motion
values are zeros, because if a point is far away from a rupture (i.e.
beyond the `maximum_distance` parameter) we assume that the
ground motion value is zero on that point.

In the case of Japan, with the parameters we are using, in average a
rupture affects only 1231 sites, since most of the sites are too far
away. So, in our estimate, we should put the total number of sites but
the effective number of sites which are affected. It quite difficult
to estimate that number on paper, but it is quite easy to infer it
heuristically.  First of all, you should reduce the original
computation by a factor of 10 or 100 times by reducing the number of
stochastic event set and or the investigation time. Then you can
perform the reduced computation in a reasonable amount of time, look
at the database and measure the number of affected sites. This will be
a decent estimation even for the full computation. Of course the full
computation will have much more ruptures, but the average number of
affected sites per rupture will be more ore less the same.

By using the effective number of sites of 1231 instead of 42921, the
estimate for the space needed goes down to 92 GB, a much more reasonable
number. Actually, even this number is too pessimistic: the number of
GMPEs has been overestimated. The important number is not the total number
of GMPEs but the effective number of GMPEs per tectonic region type.
The Japan model we are using has three tectonic region types, each with
its own GMPE: it is not that the same tectonic region type has multiple
GMPEs. Therefore in this case we can reduce to 1 the number of GMPEs and
the disk space requirement goes down to 30 GB. Of course that assumes
that the storage is as efficient as possible (8 bytes for each float)
and that nothing else is stored. Instead, a database stores much more
information, so in reality the disk space occupation for that computation
is around 60 GB. A lot, but manageable.

I actually have an experimental branch where the database structure
has been optimized so that the engine stores only 40 GB instead of 30
GB. In other words, *we are not far off from the optimal minimum*. The
secret is to store the ground motions fields in the database as
arrays, arrays that must be as long as possible: it is *much more
efficient* to store few rows with long arrays that many rows with
short arrays, i.e. storing 10 rows with arrays of 100,000 floats each
is much better than storing 100,000 rows with arrays of 10 floats
each. In short, the disk space occupation can be made relatively
efficient and it is not my biggest worry.

Much more worrysome is the issue of the saving time: at the moment the
saving time for the ground motion fields can be much bigger than the
computation time, even tens of times bigger. This is why I am changing
the database structure so that the saving becomes much more efficient,
hopefully one order of magnitude better. We will see if this is
achievable. If not, we will have to change the rules: for instance, we
could not save the GMFs and compute them on the risk side on-the-fly,
when they are needed. This is problematic when the ground motion is
correlated (which is actually the case for our computation of the
Japan) since in that case the computation is extra-slow, actually much
slower than saving the data. For that case the GMFs must be
precomputed and stored, whereas for the case of no correlation perhaps
it is better to recompute the GMFs each time during the risk
calculation.

The biggest issue on the risk side is actually reading the data and
keeping them in memory. The time to transfer 40GB at 10 M/s is a
little bit over a hour. This is not huge; the problem is that when
the data is read from the database a *lot* of memory is allocated,
much more than the nominal 40 GB (I would say something like 200GB, by
judging from previous experiences) and typically the risk computation
fails with an out of memory exception. But I will discuss that issue
in a future blog post.
