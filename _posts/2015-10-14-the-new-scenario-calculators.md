---
layout: post
title: The new scenario calculators
---

Yesterday, after over one year of work on the oq-lite project, we were
finally able to replace the old scenario calculators with their oq-lite
counterparts. The improvements in the new calculators make it possible
to simplify the workflow for the final user.

First of all, now the suggested way to use the scenario calculators is with
*a single configuration file*. In the past the user had to write two different
configuration files, one for the hazard part of the computation, conventionally
called `job_hazard.ini` and one for the risk part of the computation,
conventionally called `job_risk.ini`. The division was recommended mostly
for reasons of performance: the performance of the hazard calculation
was low, so it made sense to run it only once and then re-use the result
by following a three-step process:

1. run `$ oq-engine --rh job_hazard.ini`
2. read the hazard calculation ID printed by the job, `hc_id`
3. run `$ oq-engine --rr job_risk.ini --hc <hc_id>`

The new scenario hazard calculator is extremely fast. Normally
the hazard part of the calculation is hundreds of times faster than
the risk part. In this situation recomputing the hazard is a non-issue.
On top of that, *importing the exposure is way faster than before*:
just to give you an idea, you can import 80,000 assets in 24 seconds
on a standard laptop (tested on the exposure for Italy). The reason is
that the exposure is imported into a HDF5, which is way faster than importing
it inside a relational database. Even one million
of assets can be imported in a few minutes, i.e. a time which is negligible
with respect to the runtime of the risk calculation. The calculator is
also quite smart: usually one is only interested in a subset of the
full exposure, i.e. in the assets contained in a region described
by the `region_constraint` parameter. The engine keeps in memory
only the assets within the region, so even if the exposure is very
large you do not need to keep in memory all of it. You still need
to parse all of it and to apply the region constraint to all of the
assets, but this is fast, much faster than the subsequent risk computation.
In the near future we will make it possible to compute hazard and risk
together, in a single step

1. run `$ oq-engine --run job.ini`

where `job.ini` is a file obtained by merging together the `job_hazard.ini`
and ``job_risk.ini` files. Right now this is supported for the event based
calculator but not yet for the scenario calculators.

It should be noticed that the *old mechanism will not be
removed*. This is necessary for backward compatibility, since we do
not want to force the users to change files that worked in the past.
Therefore if you run `$ oq-engine --run job.ini --hc <hc_id>` you can
still re-use the hazard of a previous computation, if you wish to do
so.

The second difference with respect to the past, is that the ``--load-gmf``
option has been removed. In the past an user who wanted to run a scenario
risk or damage calculation against a fixed set of ground motion fields
stored in a file (say `gmfs.xml`) had to follow a three-step process:

1. run `$oq-engine --load-gmf gmfs.xml`
2. read the hazard calculation ID printed by the job, `hc_id`
3. run `$ oq-engine --rr job_risk.ini --hc <hc_id>`

Now the workflow has been reduced to a single step:

1. run `$ oq-engine --run job_risk.ini`

where in `job_risk.ini` there should be a line specifying the name
of the file with the GMFs:

  `gmfs_file = gmfs.xml`

As you see things are much easier now. The calculators are also faster
and take a lot less memory. If you have a large exposure
and a large region you may still need a reasonably large amount of memory on
the main process, but this is visible only if you have hundreds of thousands
of assets.

The third and final difference is that now *the results of the
computation are stored in the HDF5 file*, so you can easily browse them
and export them with the HDF5 tools. On the other hand the export
options of the engine are still there, and you can export average
losses, aggregate losses, loss curves and ground motion fields as
before, in NRML format and in CSV format. The CSV format available
right now is only provisional and will be revisited soon, however it is
still useful. The export speed of the ground motion fields in XML
format as been increased by hundreds of times, but it is still
hundreds of times too slow and it is consuming *huge* amounts of memory:
so we suggest NOT to export the GMFs in XML format. Exporting them
in CSV is better, but the best approach is not to export them at all:
just read the GMFs from the HDF5 file, this is easy and fast.
