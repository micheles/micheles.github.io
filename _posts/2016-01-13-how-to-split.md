---
layout: post
title: How to split correctly
---

In the [previous post](/2016/01/10/to-split-or-not-to-split/)
I noticed that the splitting procedure affects the hazard curves
and that for for event based calculations the sampling of the ruptures
depends on the splitting. The first effect is very minor and we can cope with
it. The second effect is more annoying, but fortunately there is a way
to to remove the splitting dependency by modifying the
rupture sampling logic.

The problem is that at the moment (i.e. in release 1.7) we generate a
random seed per each source: if a source is split more seeds are
generated and the ruptures sampled are different.
The solution is to *generate a random seed per each rupture*: then
even if a source a split, the rupture seeds will be the same and
the rupture sampling will not be affected.

I will give here a script illustrating the logic that will be
used in the new engine (release 1.8). You can play with it
to understand how it works. The script uses our
demo `EventBasedPSHA` as starting point and overrides some parameters
so that the computation becomes fast:

```python
oq.ses_per_logic_tree_path = 1  # reduce the number of stochastic event sets
oq.area_source_discretization = 20  # reduce the number of point sources
```

Instead of doing a full event based calculation I will consider only
the part about the sampling of the ruptures. There is a function that
returns the number of occurrencies of each rupture as a dictionary of
dictionary; for that we can extract the number of occurrencies with
`count_occurrencies` defined in the script. We want to check that the
number of occurrencies is the same, both if the area source is split
and not split (the demo has a single area source that can be split in
13 point sources with the given `area_source_discretization`
parameter).

This is indeed the case, but only because in the script we are very careful
with the management of the seeds. First we define an unique seed for each
rupture, starting from the `random_seed` defined in the `job.ini` file:

```python
src.seeds = oq.random_seed + numpy.arange(src.num_ruptures)
```

Then we make sure that when the source is split, its sub-sources get the
same seeds and in the same order; this is done with the code

```python
start = 0
for ss in sourceconverter.split_source(src):
    nr = ss.count_ruptures()
    ss.seeds = src.seeds[start: start + nr]
    start += nr
```

If you are not careful, the number of occurrences will change
depending on the splitting. Here is the complete script for
your enjoyment:

```python
import numpy
from openquake.commonlib import readinput, sourceconverter
from openquake.calculators.event_based import sample_ruptures

def count_occurrencies(num_occ_by_rup):
    occurrencies = 0
    for dic in num_occ_by_rup.values():
        for n in dic.values():
            occurrencies += n
    return occurrencies

def main(job_ini):
    oq = readinput.get_oqparam(job_ini)
    oq.ses_per_logic_tree_path = 1  # make the computation faster
    oq.area_source_discretization = 20
    csm = readinput.get_composite_source_model(oq)
    csm_info = csm.get_rlzs_assoc().csm_info
    [src] = csm.get_sources()  # there is a single source
    # build an array of unique seeds of size num_ruptures
    src.seeds = oq.random_seed + numpy.arange(src.num_ruptures)

    print 'Calculation with area source unsplit, total ruptures', \
        src.num_ruptures
    print count_occurrencies(
        sample_ruptures(src, oq.ses_per_logic_tree_path, csm_info))

    sources = list(sourceconverter.split_source(src))
    print('Calculation with area source split in %d sources' %
          len(sources))
    start = 0
    occurrencies = 0
    for ss in sourceconverter.split_source(src):
        nr = ss.count_ruptures()
        ss.seeds = src.seeds[start: start + nr]
        start += nr
        occurrencies += count_occurrencies(
            sample_ruptures(ss, oq.ses_per_logic_tree_path, csm_info))
    print occurrencies

if __name__ == '__main__':
    main('/home/michele/oq-risklib/demos/hazard/EventBasedPSHA/job.ini')
```
