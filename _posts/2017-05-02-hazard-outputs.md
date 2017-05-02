---
layout: post
title: Changes in the hazard outputs
---

In the few last years the engine has become more and more
efficient. Nowadays it is so powerful that design decisions that were
reasonable 7 years ago are now questionable. In particular, as we
scale up the size of our computations, the management of the hazard
outputs has to change. In the past only computations with with a
relatively small output were feasibile, so it made sense to export everything
with a single call. This is no more feasible.

Statement of the problem
---------------------------------

Let's consider the SHARE computation for Europe: 7 years ago, at the beginning
of the engine, it was an impossibly large computations that could not be
completed: only partial computations by tectonic region types
were performed, supplemented by a large amount of manual postprocessing.
Nowadays it is a routine computation that the engine can performs in a few
hours in our cluster. Still, even if the core computation is small for today
standards, the output generation part is still huge and challenging.
Here are the figures:

```
number of hazard sites N = 126,044
number of hazard levels L = 312
number of realizations R = 3,200
size of the hazard curves using 32 bit floats: 4 * N * L * R = 469 GB
```

As it is now, by default the engine produce all of the hazard curves
and the time spent ther is longer than the time to perform the core
calculation. In order to work around this issue there is flag in the
`job.ini` file called `individual_curves`: by setting it to `false`
only the statistics are stored, say the mean hazard curves: this
requires 3200 times less space, i.e. only 150 MB. Unfortunately,
regular users do not read the fine points of the manual and they do
not know about this flag.  Also, since now we have a web frontend to
the engine (the WebUI) any user clicking on the link to download the
hazard curves will start a full export procedure taking hours/days and
producing hundreds of gigabytes of data. The export may even kill the
server and the result will be to big to download anyway.

The solution
----------------

For this reason we are changing the behaviour of the engine:
starting from release 2.4 the engine will only export the statistical
outputs. There will be no way to export the full outputs from the WebUI
with the single call: you will have to export one realization per call.
It will still be possible to export all of the realizations with a
single call, but only from the command-line interface, locally, with the command

```
$ oq export hcurves/all
```

This export will be slow for large computations and it may generate
enourmous amounts of data, depending on the number of sites and realizations.
If you are interested in postprocessing the hazard curves with a custom
algorithm, the recommended way is to do it programmatically in Python,
thus bypassing the monolithic export procedure.
Here is a trivial example that should get you started:

```python
>>> from openquake.commonlib import datastore, calc
>>> dstore = datastore.read(42)  # assuming 42 is the calculation ID
>>> imtls = dstore['oqparam'].imtls  # intensity measure types and levels
>>> sitecol = dstore['sitecol']  # the site collection
>>> pgetter = calc.PoesGetter(dstore)  # instantiate the getter
>>> for rlz in pgetter.rlzs:
...    # extract the curves for the given sites and realization
...    print(pgetter.get(sitecol.sids, rlz.ordinal).convert(imtls))
```

will print the hazard curves for each realization as a composite array of N
elements, being N the total number of sites.
