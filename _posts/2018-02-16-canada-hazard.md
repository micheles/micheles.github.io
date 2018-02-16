Running extra-large PSHA calculations (Canada 2015)
---------------------------------------------------

In recent years the engine has become so good that it is able to run
almost any calculation without tweaking; this is why I have
not updated this blog for several months. But now I have found a
calculation large enough to make for an interesting blog post: the
Canada 2015 National Hazard Model.

Computationally, the Canada model is interesting because it has really a lot
of sites (206,366) and of realizations (13,122); still it is small enough
that it can be run with full enumeration, if one is careful enough. Moreover,
it is interesting because it features a lot of duplicated sources and can
be used as a test bed for a recently introduced feature
(`optimize_same_id_sources`).

Here I will discuss what tricks that are needed to run the Canada model
and any hazard model with a similar size.

Optimizing away the duplicated sources
--------------------------------------

The first thing to do, since we know that the model has duplicated
sources, is to look for them. The source model logic tree for the
Canada model has the form

```xml
    <logicTreeBranch branchID="b1">
        <uncertaintyModel>./nwH_swR_neH_seH.xml</uncertaintyModel>
        <uncertaintyWeight>0.24</uncertaintyWeight>
    </logicTreeBranch>
    <logicTreeBranch branchID="b2">
        <uncertaintyModel>./nwH_swR_neH_seR.xml</uncertaintyModel>
        <uncertaintyWeight>0.12</uncertaintyWeight>
    </logicTreeBranch>
    <logicTreeBranch branchID="b3">
        <uncertaintyModel>./nwH_swR_neH_seY.xml</uncertaintyModel>
        <uncertaintyWeight>0.24</uncertaintyWeight>
    </logicTreeBranch>
    <logicTreeBranch branchID="b4">
        <uncertaintyModel>./nwH_swR_neR_seH.xml</uncertaintyModel>
        <uncertaintyWeight>0.16</uncertaintyWeight>
    </logicTreeBranch>
    <logicTreeBranch branchID="b5">
        <uncertaintyModel>./nwH_swR_neR_seR.xml</uncertaintyModel>
        <uncertaintyWeight>0.08</uncertaintyWeight>
    </logicTreeBranch>
    <logicTreeBranch branchID="b6">
        <uncertaintyModel>./nwH_swR_neR_seY.xml</uncertaintyModel>
        <uncertaintyWeight>0.16</uncertaintyWeight>
    </logicTreeBranch>
```

and is built on top of 6 underlying source models. The 6 basic source
models are not independent, i.e. the same source can appear or more
than one model, even in all 6 of them. If the same source
appears in all 6 source models and the flag `optimize_same_id_sources`
is set, then its calculation will be 6 times faster, so the
optimization is quite significant.

There is a simple way of knowing which sources are duplicated and
how many times are duplicates without running the calculation: the
command

```bash
$ oq info job.ini
```

This command will also print on the screen some information about the
logic tree and the maximum number of realizations. The interesting
part of the output for the duplicated sources will look like this:

```
source_id              multiplicity
====================== ============
20130709_WA_H_Model_v6 6           
ACM                    3           
ACM_4                  6           
ADR2                   2           
ADRN                   4           
ADRS                   4           
AID                    6           
AIS                    6           
AKC                    6           
...
``` 

As you see several sources appear 6 times (`20130709_WA_H_Model_v6,
ACM_4, AID, AIS, AKC, ...`), some appear 4 times (`ADRN, ADRS, ...`),
some three times (`ACM, ...`) and some 2 times (`ADR2, ...`).
The more duplicated sources there are, and the higher the multiplicity,
the more substantial the effect of the optimization.

In the case at hand I ran the model both with the optimization (in 6h39m)
and without (in 17h42m). In the heavy computational part in the workers
the speedup is more than three times (3.3x), so very substantial.

Computing the statistics
-----------------------------

Recent versions of the engine do not store the hazard curves for individual
realizations, but only statistical results like the mean hazard curves and
the quantile hazard curves. However a few simple multiplications will make it
clear that computing even the mean curves is a quite difficult task.

The Canada model has 5 intensity measure types, each one with several
intensity measure levels; in total a single hazard curve is represented
as an array with 107 elements. Since there are 206,366 sites and 13,122
realizations and each floating point number requires 8 bytes of memory
to be allocated, to compute the mean hazard curves one has to keep in memory
at least

  107 x 206,366 x 13,122 x 8 = 2,317,992,062,112 bytes

i.e. more than 2.1 TB of data. In a cluster with 160 cores, assuming
equidistribution of the memory, this means 13.5 GB of RAM per core.
In reality the needed memory will be a lot more than
that, since the engine is doing more than just keeping in memory the
arrays. It is clear therefore that we will have to tweak the parameter
concurrent_tasks to produce enough tasks that the computation can fit
in memory. The way to do that is via trial and errors, and I discovered
that in our cluster one has to set

  concurrent_tasks = 2,000

in order to get the calculation running within the memory constraint we
have, i.e. 3 GB per core.

There is yet another problem with statistics, though: you cannot compute
them directly. If you try, you will get an error like this:

```python
       return dumper(obj, protocol=pickle_protocol)
   kombu.exceptions.EncodeError: cannot serialize a string larger than 4GiB
```

The issue is that direct computation of the statistics requires transferring
information about the hazard curves from the controller node to the workers
and that transfer is done via celery and rabbitmq. Such technologies have
limits and cannot transfer amounts of data that exceed the limits.
This is the case for the Canada calculation. Therefore in the job.ini file
one has to set

  mean_hazard_curves = false
  
to make sure that the engine does not try to compute the statistics directly.
Instead, we have to compute the statistics indirectly, in post-processing.

The thing you should understand is that the engine is very smart: so smart that
even if you disable the statistics it will still save in the datastore
enough information to build them later. Actually, it has enough information
to extract all realizations.

To build the statistics in postprocessing you should write a file
`job_stats.ini` with the following content:

```bash
$ echo job_stats.ini
[general]
description = Canada 2015 National Hazard Model Stats
calculation_mode = classical
concurrent_tasks = 2000
mean_hazard_curves = true
```

and then run

```bash
$ oq engine --run job_stats.ini --hc PREV_CALC_ID
```

where `PREV_CALC_ID` is the ID of the previous calculation.

This is not all. On a cluster, the engine will still try to use
celery/rabbitmq, so the calculation will still fail. The solution is to
configure a shared directory, i.e. a directory where the controller node
can save the calculation .hdf5 files and the workers can read them and
to specify the location of that directory in the `openquake.cfg` file.
Only then the engine will be able to read the data from the original
calculation directly from the workers, without using celery/rabbitmq
and without pickling, i.e. in an efficient way. So efficient that
the calculation was actually done in less than half an hour on our
cluster.
