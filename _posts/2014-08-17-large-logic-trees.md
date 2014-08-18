---
layout: page
title: PSHA calculations with large logic trees
---

Today's post will collect some information about classical PSHA
calculations with large logic trees, in particular about the SHARE
model. As a test bed, I will use a reduced version of the SHARE model,
considering a single intensity measure type ('PGA'), only 50,000 sites
instead of the full 126,044 sites and only the submodel defined in
`as_model.xml`. The reduced model is still taking into account all of
the logic tree branches, i.e. 1280 realizations, so
the computation is pretty large.

The numbers of the reduced model are the following:

Parameter        | Value
-----------------|--------
num_sources      | 555,157
num_ruptures     | 7,751,390
num_sites        | 50,000
num_levels       | 26
num_realizations | 1280
num_tasks        | 671

The reduction is necessary because currently the full SHARE model
cannot addressed as a single computation: the quantity of data to return
from the workers is too big and the celery/rabbitmq combo fail. After
all such libraries were designed to exchange a lot of small messages
and not a small number of huge messages. Moreover the full model
has out of memory problems. Here are the numbers for the reduced
model instead:

Memory Measure   | Value
-----------------|--------
haz_curves_mem   | 12.4 GB
post_proc_mem    | 24.8 GB
disk_space_mb    | 22,947
max_mem_per_core | 113 MB

The memory allocation of the hazard curves has been computed by
counting 8 bytes per float; then 50,000 * 26 * 1280 * 8 = 12.4
GB. This is quite less than the memory occupation on the database,
which is of 22.4 GB.  The memory occupation in the database could be
reduced significantly, as discussed
[before](/2014/06/28/gmpe-logic-tree/), and the saving time could be
reduced by a factor of 60 or more; at the moment, however, the saving
time is quite significant, and actually it is comparable with the
computation time:

Operation          | Time
-------------------|------
compute hazard curves | 5h50m
save hazard curves | 4h12m
compute mean curves| 24m

In the full model the saving time would dominate. Another interesting
time is the time spent in aggregating the hazard curves; in the
reduced computation it is pretty insignificant (6 minutes) but it may
grow significantly in the full computation (or not: that must be
seen).  Certainly if the number of cores grows the aggregation time
will become the limiting factor; at the moment it seems that we are
not there, yet.

The time to compute the mean curves is now very small (less than 24
minutes); before a recent change it would have been over 2 days,
involving a lot of heavy database queries.  Nowadays the curves
are being kept in memory; that involves an increase of the memory
consumption in the saving phase and a peak in
the post-processing phase. Actually, with the current implementation,
at maximum the post-processing phase requires an additional amount of
memory equal to the memory taken for the hazard curves of the largest
Intensity Measure Type; for a single IMT, the total memory occupation
is doubled.
