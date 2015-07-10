---
layout: post
title: New generation calculators: the ebr calculator
---

The release 1.5 of the OpenQuake engine will bring with it the first
of a new generation of calculators: the ebr (short for event based
risk) calculator. The new generation calculators will be [based on the
datastore](/2015/06/14/introducing-the-datastore/), not on Postgres,
and they will not distinguish between hazard and risk. In other words,
it will be possible to use a *single configuration file specifying
both the hazard parameters and the risk parameters*.

This "great unification" of hazard and risk is something that I have
being struggling to achieve for years: the current separation is purely
artificial, due to the fact that in the past we had different
developers for hazard and risk. Now I have everything in hand and
it does not make any sense to keep separated the two parts.

The old event based calculator was slow because the hazard was made by
one team and stored in the database to be used by the other team; but
now I known both hazard and risk and I can make a risk calculator
which is able to compute the hazard on-the-fly and can be thousand of
times faster, since it does not need to write and read large amounts
of data. Also, there is a huge simplification of the data structures,
from a complex relational structure to pure numpy arrays that live in
memory.

To show off the improvements, I will give some numbers for a calculation
about Turkey, that could not be performed in the past, but which is
easy with the new ebr calculator. The calculation has the following
parameters:

Number          | Value
----------------|-------
num_assets      | 10,626
num_sites       | 927
num_realizations| 192

The old calculator needed to save the GMFs on the database: just
to give you an idea of the time that was wasted there, here are
some numbers, in a situation with a database half-empty and with
2048 tasks:

Operation              | Cum. Time
-----------------------|-----------
computing gmfs         | 35,125 s
saving gmfs 	       | 1,070,300 s

As you see, the saving time is 30 times bigger than the computation
time.  This already should tell you that saving the GMFs in the
database is a bad idea; also, during the computation *the database
size increased by 207 GB!* That means that it is very easy to run out
of disk space: also, the bigger the database, the slower the
queries. Indeed, the real problem is not the saving time, nor the
database size, it is the reading time: *the reading time is infinite*!
By that, I mean that it is impossible to read all the needed GMFs in
the risk calculation: the database fails, it becomes as slow as a
rock, and at a certain moment the risk calculator runs out of
memory. Complete failure.

How we run this calculation, then? The answer is that we did not run
it, truly.  Instead we used a workaround, and we run several small
calculations, one for each hazard realization. There were 192
realizations and each reduced calculation was still slow, so after 4
days of computation we run out of time and stopped having considered
half of the branches or so. Also, the export time was very
significant, comparable to the neat computation time.

Just to give you an ides, there were the figures for a typical run with 518
tasks, which took ~30 minutes to run and ~ 30 minutes to export:

Operation              | Cum. Time | Memory
-----------------------|-----------|--------
computing individual risk | 7,633 s| 163 M
getting hazard | 203,076 s| 59 M

As you see, the computation is still dominated by the reading time from
the database, 203,076 cumulative seconds, which is 27 times slower than
the calculation time. This just for a single realization: for the full
computation the reading time would have been much longer, more than
192 times longer, since in such conditions of high stress the performance
of the database become disastrous. The computation would have required
163 M * 192 rlzs = 30 GB of memory per core, i.e. 15 times more
memory than we have, since we have 2 GB per core. That explains why
we ran out of memory.

If we summed the time needed to compute all the branches, plus the time to
export all the results from the database, our estimate was over a week.
Not to mention that one had to write a custom script to post-process the results
and to aggregate them, and that also took time. Fortunately, there was no
risk of running out of disk space, since the database was growing of ~300 M
per branch, i.e. it would take "only" 56 G to store the event loss table
in the database.

So the situation was a total disaster and has been known to be a total
disaster from the first day we run a risk calculation on our cluster over two
years ago. Users have complained about this situation for over a year.
The problem was that in order to solve this we had to essentially rewrite
the architecture of the engine.

To throw away the engine and to rewrite from scratch the
event based calculator would have been much simpler than what we did.
For over a year we tried to cope with the existing architecture, doing
a lot of improvements, but last summer it become clear that a total
revolution was needed. So we started the oq-lite project, we rewrote
*all* the calculators by carefully comparing all results with the
engine ones. In the process we found several bugs/problems/issues
(especially with the management of large logic trees and sampling, which was
fundamentally broken) and we fixed them both on oq-lite and on the
engine.  We also implemented a compatibility layer between oq-lite and
the engine, so that now the engine is able to use the oq-lite
calculators.  Today, after 10 months of the start of the oq-lite
project, we have an ebr calculator in the engine that is totally free
from the database bottleneck. Here are the figures:

Turkey full computation  | ebr calculator, 2048 tasks | old event based calculator, 512 tasks
-------------------------|----------------|----------------------------
Total disk space | 1.9 GB | estimated ~263 GB
Max mem per core | 1.3 GB | estimated ~30 GB
Computing individual risk | 2,363,544 s | estimated 1.5 million s
Getting hazard | 33,945s | estimated > 40 million s
Total run time + export   | 3h 15m | estimated ~200 hours

Basically, recomputing the GMFs on-the-fly is more than 1000 times
more efficient than reading them from the database. The memory
consumption is over 20 times smaller. The required
disk space is more than 100 times smaller. The export time is now
zero, because the event loss table is already stored in a perfect
format for the visualization and analysis tools inside the .hdf5
file generated by the calculator. There is no need to aggregate
partial results, since everything is done in a single step.

In short, the impossible is now possible.
