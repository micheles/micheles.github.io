---
layout: page
title: Large Event Based Risk Calculations
---

Hazard calculations have received a lot of attention recently,
so much that now they can scale up to logic trees with a few
hundreds of realizations without particular issues. The only
problem, [as I documented before](/2014/08/17/large-logic-trees/), is
the saving time on the database, which is 
normally acceptable, unless you want to scale up to over
a thousand realizations (i.e. the full SHARE model).

On a specific region of interest, usually one does not need
the full SHARE model, because some tectonic region types
may be missing in that region, so that the logic tree
can become significantly smaller. For instance we have
a computation for Germany, which we use as a test bed for
our optimizations, that requires only 100 realizations
out of the complete logic tree of 1280 realizations.
100 realizations are a snap and the hazard computation
can be done in a hour or so in our cluster.

The problem is the risk. The risk is an entirely different
story. A risk computation based on a hazard computation
with 100 realizations and a few thousand sites is really
*really* big. So big that, in fact, it cannot be performed.
I tried to run it on our cluster and on other machines
and I could not finish it. The problem is with rabbitmq:
the data transfer is so big that rabbitmq dies and stop
responding. I have seen situations where rabbitmq takes
more than 35 GB of RAM, as well as over 35 GB of disk
space non the mnesia directory. In such situations the
only solution is to kill rabbitmq brutally and to delete
manually the mnesia directory. We are at the limit of
the tecnology, rabbitmq was not designed to transfer
such huge amount of data.

Fortunately, not all hope is lost. I do have an experimental branch
where some of the data which currently are transferred via rabbitmq
have been stored in the database and transferred via postgresql.
Databases have been designed to manage large amount of data, so in
that branch it is possible to run the computation to completion. In
doing so, however, I have discovered other bottlenecks, some
expected, some unexpected.

Here are some numbers:

Parameter        | Value
-----------------|--------
num_sites        | 8215
num_assets       | 16430
num_imts         | 1
num_realizations | 100
num_ruptures     | 48,798
num_tasks        | 166

The expected bottleneck is the database, in particular the time spent
in reading the ground motion fields, which is over 45x times bigger
than the computation time!

Operation | Cumulative time
----------|-----------------
getting gmfs | 1,681,964 s
computing individual risk | 36,941s

This is a very serious problem, but it is expected, because we had
this issue from the very beginning. The problem is that the selection
queries are slow because 1) there are a lot of ground motion fields
and 2) they are stored in the database in an inefficient way.

The unespected and positive thing is that in this branch the
memory occupation is very low, we are using not even the 10%
of the memory we have available on the cluster.
The unexpected and negative thing is the following:

Operation  | Cumulative time
-----------|-----------------
agg_result | 1,290 s

Over 20 minutes are spent aggregating the results, and that happens
on a single core. Even if we manage to improve the situation on
getting the ground motion fields (and I am confident that we
can gain at least an order of magnitude) the aggregation time
will become the new bottleneck. But this is a problem that will
wait for the future. The issue with the ground motion fields
is more urgent, because it scale terribly bad with the number
of cores. More cores you have, more queries are performed,
more the database is stress, and slower the computation is,
to the point that it is faster on a single machine with 32 cores
than on a cluster with 256 cores (I have tried it).
