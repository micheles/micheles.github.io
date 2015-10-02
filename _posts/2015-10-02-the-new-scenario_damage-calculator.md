---
layout: post
title: The new scenario damage calculator
---

We are now ready to replace the old postgres-based scenario damage calculator
with the new HDF5-based calculator. The only thing left is a performance
analysis for large calculations, to make sure that there are no
regressions. To this aim, I have analyzed the case of the largest
scenario damage calculation I have at hand: Portugal onshore with 268,056
assets distributed on 4,050 sites. There are 8 different intensity measure
levels, 81 taxonomies and a large risk model with several different
fragility functions.

scenario hazard: from 17 minutes to 1.7 minutes
-----------------------------------------------

A scenario_damage calculation requires the ground motion fields to be
computed first; this is done by the scenario hazard calculation.
While the GMFs computation is quite fast (there are
only 4,050 sites and 3,000 realizations) the postgres-based calculator
is plaged by a number of inefficiencies. A lot of the time
is spent during startup while saving the assets and the sites in the database,
and then a lot of time is spent saving the GMFs in the database.
The calculation time is negligible. Here are some measurements with
the current master:

Operation              | Time
-----------------------|-----------
saving the exposure    | 11m 9s
saving the sites       | 41s
saving the GMFs        | 4m 57s
GMF calculation        | 8.5s
*total duration*       | 16m 56s

As you see, 12 minutes were lost in the pre-execute phase just to store
the assets and the sites and 5 minutes were lost in the post-execute
phase to save the GMFs; the actual computation took only 8 seconds.
It is clear that the hazard calculator will benefit *a lot* from
the HDF5 conversion, since this is a calculator which is totally
dominated by database issues. Indeed, here are the times for the
new calculator:

Operation              | Time
-----------------------|-----------
reading the exposure   | 1m 36s
GMF calculation        | 8.4s
saving the GMFs        | 1.2s
*total duration*       | 1m 48s

The memory occupation on the workers is negligible. In the controller node
instead we need 3.2 GB to keep in memory the large exposure.

For what concerns the disk space occupation, the old calculator increased
the database size by 1472 MB, whereas the new one produces a HDF5 file
of 871 MB; most of the space is taken by the GMFs (788 MB).

scenario damage: from 1h 20m to 1h 22m
-----------------------------------------------

The risk part of the computation is not dominated from the database,
so one should not expect a big speedup. Indeed the new calculator
takes the same time of the old one and the time depend very much
on the balancing of the task distribution. The way to improve it is to make
sure that there are no slow tasks dominating the computation. The time of
1h 22 minutes has been obtained with concurrent_tasks=512, which is the
usual one in our cluster. There is room to improve here, by improving
the weighting algorithm of the tasks.

On the other hand, one should expect a definite memory saving: the old
calculator was reading the GMFs from the database, as very
memory-expensive Django objects, whereas the new calculator is reading
the GMFs are numpy arrays transferred via rabbitmq. Here are the
numbers:

Memory per core (old) | Memory per core (new)
----------------------|----------------------
882 MB                | 42 MB

We are using 20 times less memory!

Moreover, the new calculator is not doing some useless operations
performed by the old calculator. For one, the old calculator was
building the epsilons even in the case of a scenario damage
calculator, that does not need them! Building the epsilons
took 2,171 cumulative seconds (which is very little, divided by
256 cores) and now is zero; saving the damage statistics on the
database took 2,201 seconds (again little) and now is essentially
zero since saving in the datastore is thousand of times faster.

Those are minor speedups, so the runtime did not change significantly
and it is not easy reduce it. Right now the cumulative time for the
calculation in the workers is of 879,914 seconds; divided by 256 cores
it means 57 minutes, so if we had perfect distribution of the load the
computation should run in 1 hour or so. This is the lower limit we can
reach with the current risk algorithm, which is the same between the
old and new calculator.
