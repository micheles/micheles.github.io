---
layout: post
title: The new GMFs and hazard curves calculator
---

Historically, the biggest bottleneck of the event based hazard calculator
was the storage of the ground motion fields. An HDF5 file
is way more efficient than Postgres for this task, so the new
calculator uses this approach. Moreover, in the case of complex logic
trees, it avoids storing redundant data. The two optimizations combined
produce an impressive (actually an insane) speedup. Let me show off the
improvement by considering a few specific cases.

The case of a single realization
--------------------------------------

Let's start from the good old [Miriam's island](
/2013/05/17/the-story-of-Miriam-island/), which is a computation with
1,792 sites and a lot of ground motion fields, (4.6 GB of them). In
such case the old calculator gives the following figures, starting
from a database half empty and with the parameter `concurrent_tasks`
set to 1000:

Operation              | Cum. Time| Memory
-----------------------|----------|--------
computing gmfs         | 9,348 s  | 80 MB
saving gmfs 	       | 13,119 s | 28 MB

As you see the saving time is bigger than the computing time. It is
actually not much bigger, because in the past we did a lot of
performance improvements, but originally the saving time was
dozens of times bigger than the calculation time. Still, with the
new calculators the numbers are much better:

Operation              | Cum. Time| Memory
-----------------------|----------|--------
computing gmfs         | 4,450 s  | 1 MB
saving gmfs 	       | 11 s     | 0.19 MB

As you see, the improvement in the saving time is incredibile: from
13,119 to 11s! A factor of 1200x!!

On top of that, the computing time has been reduced by more than half:
this is possible because we are saving a lot of time when allocating
memory. The old calculator was using dictionaries and lists of Django
objects: the new calculator uses numpy arrays. So the same computation
requires 80 times less memory. The abysmal difference in the saving time is
explained by the fact that the GMFs are saved sequentially as numpy
arrays on a HDF5 file instead of doing parallel bulk imports in
Postgres with 256 workers writing simultaneously.

The case of a large logic tree
--------------------------------

Whereas Miriam's island is a good test case, it is even more interesting
to look at a real life case, like the Germany computation,
which is being used by one of our sponsors. This is a case with not many
ruptures (only 48,918) but with a lot of GMFs because there are 8,232 sites
and a complex logic tree with 100 realizations (it is a SHARE
computation). In such a case an even bigger speedup is expected, since
the new calculator takes a great
care to avoid saving more ground motion fields than needed.
To understand this point, you first must digest the
[concept of effective realizations](http://docs.openquake.org/oq-risklib/master/effective-realizations.html). Read the documentation before continuing.

THe important point is that it is
possible to generate the ground motion fields corresponding to all
realizations from the (much smaller) set of GMFs corresponding to the
realization associations. It is possible to compute the size of the
reduced GMFs with the following formula:

```python
   nbytes = 0
   for rupcol, gsims in zip(collections, rlzs_assoc.get_gsims_by_col()):
       bytes_per_record = 4 + 8 * len(gsims) * num_imts
       for rup in rupcol.values():
           nbytes += bytes_per_record * num_affected_sites(rup)
```

Here `collections` is an array of dictionaries; each dictionary
contains ruptures keyed by a string (the so-called "tag"). The rupture
dictionaries are numbered, and their ordinal is called `col_id`
(collection ID). The method `rlzs_assoc.get_gsims_by_col` returns the
associations `col_id -> list of GSIMs`. Notice that the details will
likely change in the near future, in particular I may replace the
dictionaries of ruptures with arrays of ruptures.

The size of a GMF record in the HDF5 file is 4 bytes for the ruptured index
(it is an unsigned 32 bit integer) plus 8 bytes for each float; the number
of floats per record is `num_gsims * num_imts` where `num_gsims=len(gsims)` is the
number of GSIMs associated to the given rupture collection and `num_imts`
is the number of Intensity Measure Types.
In the case of full enumeration there is a rupture
collection for each tectonic region type, otherwise the number of
rupture collections is equal to the number of samples times 

The size of the full GMFs (i.e. for all realizations) is given by
the formula

```python
   nbytes = 0
   for rlz in rlzs:
       col_ids = list(rlzs_assoc.csm_info.get_col_ids(rlz))
       for rupcol in collections[col_ids]:
           bytes_per_record = 8 + 8 * num_imts
            for rup in rupcol.values():
               nbytes += num_affected_sites(rup)
```

and it is much larger. For instance, we can consider the case of Germany.
This is an event based calculation using the SHARE model, with 100
realizations and 8232 sites, i.e. a pretty large calculation.
The size of the GMFs is

- Germany, all realizations: 17.67 GB
- Germany, compact format: 1.31 GB

In other words, the compact format is 13+ times smaller than the
full format. The saving time is proportionally smaller. On top
of that, the storage on the database is particular inefficient
in this case (technically it is because we are storing short arrays)
so that the old calculator is storing around 46 GB of data. This
includes the ruptures, which however are smaller than the GMFs.
The saving time on the database is affected by the high level
of concurrency (I run this computation with 1000 tasks on a cluster
with 256 cores), by the fact that the database was half full, and
of course by the various database constraints (primary keys and
others). So the HDF5 saving is expected to be much faster.
In reality it is insanely fast. But let me first show the
numbers for the computation times:

Operation              | Cum. Time| Memory
-----------------------|----------|---------
computing gmfs (old)   | 3,769 s | 29 MB
computing gmfs (new)   | 2,375 s | 0.73 MB

The speedup when computing the GMFs is consistent with our findings of
before (it is significant); in particular it requires a *lot* less memory,
40 times less memory. This is the advantage of using numpy arrays and
not Django objects.

The situation for the saving times is beyond imagination:

Operation              | Cum. Time| Memory
-----------------------|-----------|-------
saving gmfs (old)      | 636,613 s | 4 MB
saving gmfs (new)      | 3.2 s   | 0.25 MB

We went from 636,613 s to 3.2 s, a factor of 200,000 times!!


Generation of hazard curves
--------------------------------

The new calculator is also able to generate hazard curves from the GMFs
and to save the curves without saving the GMFs, just as the old calculator.
But clearly the new calculator is faster. Here are
some numbers for Miriam's island with 256 tasks:


Operation              | Cum. Time| Memory
-----------------------|----------|---------
 (old) total compute_gmfs_and_curves | 10,483 s | 77 MB
 (new) total compute_gmfs_and_curves | 8,153 s | 131 MB


It is not clear to me why we are using more memory, it is something
that I have yet to investigate.


The case of sampling
--------------------------------

The new calculator is still not reliable in the case of sampling, so I
will not provide any figure for this situation. I will write a separate
blog post when this use case will be under control.
