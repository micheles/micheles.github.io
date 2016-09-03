---
layout: post
title: Recent progress in the classical PSHA calculator (SHARE)
---

The OpenQuake engine has always been about large calculations: however, now
we want to tackle *huge* calculations, something like the UCERF model of
the United States. So I spent my summer paving the way for that project
and optimizing the engine in the case of really large computations.

Historically, the most important classical calculation we ever did was the
SHARE calculation for Europe: this calculation is the reason why the
engine was implemented first and its original test bed. The SHARE project was
completed before the release 1.0 of the engine, and it used a code based
totally different from what it is the engine now. At the time it took
weeks of calculations plus weeks on manual postprocessing. It was totally
impossible to run the full calculation, so it had to be split in tectonic
region types and then the probabilities has to be composed manually. It
was a really tough calculation, who could not be done out of the box and
therefore very tricky to reproduce, because of the undocumented manual steps.

In June we released the OpenQuake engine 2.0, which is a total rewrite of
the original engine, and we expected it to be much faster, also for the
SHARE calculation. It turns out that it was really fast, even more
than expected, but the computation could not be done, again :-(

In order to understand the issue, let me give some numbers; the SHARE
computation has

number of hazard sites N = 126,044
number of hazard levels L = 312
number of realizations R = 3,200

Using 8 bytes per float the sheer size of the generated hazard curves
is 8 * N * L * R = 938 GB i.e. nearly 1 terabyte of data. This is not
much, the issue was that in order to compute mean and quantiles of the
hazard curves the engine had to keep all of the curves in memory at
the same time and we do not have 1 terabyte of memory!  I was very
aware of this issue, that only affects really large computations:
SHARE is the only one we have at the moment that it is large enough to
run into this problem. For this reason I did not stop the release of
engine 2.0 and postponed the solution of the memory issue to engine 2.1.

The good news is that the issue is now solved: by using
the current master you can run the full SHARE to completion by using
less than 65 GB of RAM. The solution was to parallelize the computation
of the statistics. The engine 2.1 split the sites in a number of tiles
more or less equal to the number of realizations (in this case
126,044 sites / 3,200 realizations ~ 39 sites per tile) and compute
hazard curves and statistics one tile at the time: the maximum
memory needed per core is of the order of

`N x L = 300 MB`

i.e 3200 times less than before. Notice that this is done in parallel
and not sequentially: around 3200 tasks are generated each one
containing all the realizations. Since the engine is doing some
approximation in this case 3152 tasks are generated: 3151 tasks have
tiles of 40 sites each, whereas the last tile has only 4 sites. The
numbers add up as follows:

`3151 task * 40 sites + 1 task * 4 sites = 126, 044 sites`

The tiles here have nothing to do with the tiles in the first part of
the computation: the computation of the statistics happens in a different
calculator than the computation of the probability maps. This means that

*you can change the quantiles in the job.ini file and recompute the
statistics without having to repeat the full computation!*

This has been a much wanted features for years and has been implemented
in engine 2.0. Since the memory problem has been solved, now you can take
full advantage of it. It should also be noticed that the engine has a flag

`individual_curves=false`

that should be set to false in this kind of calculations (the default
is true).  After all, you don't want to look at 3200 realizations
one-by-one, typically you are interested in mean and quantiles. The
engine still has to compute all the realizations, but it does not need
to store all of them: it needs to store only the mean and the
quantiles; in the share case we have

```
mean_hazard_curves = true
quantile_hazard_curves = 0.05 0.16 0.5 0.84 0.95
```
so 1 (mean) + 5 (quantiles) = 6 curves has to be stored, not 3200;
each curves requires 0.293 GB, so 1.758 GB are enough to store the
results. If you set `individual_curves=false` the computation
is fast since you do not have to send back the curves
for all realizations and store them; in fact, you can compute the
statistics for the full SHARE model in 11 minutes!

Here are some numbers:

operation                     | cumulative time
------------------------------|-------------------
compute stats                 | 57,593 s
combine pmaps                 | 13,864 s
saving hcurves and stats      | 695 s

`combine pmaps` is the operation of converting the probability maps
(there is a map for each tectonic region type) into hazard curves
(this is the operation that was done in manual postprocessing years
ago): as you see, it is a pretty fast operation compared to the computation
of the statistics, which is dominated by the quantiles. Then the saving
time is not much, 11 minutes and 35 seconds. All this post-processing
operations are still ridiculously fast compared to the sheer size of the bulk
computation:

operation            | cumulative time
---------------------|-------------------
computing poes       | 5,470,790 s
making contexts      | 411,698 s
managing sources     | 13,352 s

As you see, most of the time is spent computing the probabilities
of exceedence, over 5 millions of seconds in total: it looks a lot,
but it is half of the time needed for our model of South America.
SHARE is not a large computation anymore: the point to bring home
is that

`nowadays the full SHARE with 3200 realizations runs in 9 hours 30 minutes*

And that's all.
