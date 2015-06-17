---
layout: post
title: Analyzing large PSHA hazard calculations (1)
---

How big is a PSHA calculation? Will I be able to run it on my
machine (or cluster) or will the calculation run out of memory? How much
time will it take to run it to completion?  Such questions are clearly
very relevant and are asked nearly every day by the OpenQuake Engine
users. After all, the engine is engine is meant for state-of-the-art
computations, that stress the limits of technical feasibility, so it
is quite common to be unable to run a large computation for various
technical obstacles.

Unfortunately, it is quite difficult to estimate upfront the size of
a computation, and estimating the memory occupation and runtime is
particularly challenging. Nevertheless, a few things can be said, and
oq-lite provides some commands to facilitate the work of a hazard
and risk analyst. To estimate the size of a risk calculation is
more difficult than to estimate the size of a hazard calculation;
and the analysis of an event based calculation is more difficult
that the analysis of a classical PSHA calculation. In this post
I will only consider the simplest possible case, a classical
PSHA without tiling.

Even the simplest possible case is not easy, since things are different
depending if you are using the engine calculator or the oq-lite calculator.
The calculation speed of the two calculators is more or less the same,
but when it comes to saving and exporting the results the oq-lite calculator
is significantly better (*orders of magnitude better*).
Moreover, the performance figure of the calculators are in constant state of
flux, because we work on the calculators all the time and they are subject
to drastic changes, usually for the better. If a calculator becomes
slower or more resource intensive it is likely a bug and should be reported.

Having said that, let's try extract the most reliable information we
can extract, i.e. the size of the generated output. Even that is not
obvious in the engine, since the data is stored in several relational
tables and it is difficult to estimate precisely how much disk space will
be needed. Thus, I will perform my analysis for the oq-lite calculator,
which is storing the data in a HDF5 file, which size can be estimated
just with a simple multiplication of the input parameters.

Let's start from the case of a simple calculation producing only hazard
curves and let's ignore hazard maps and uniform hazard
spectra.  Currently hazardlib is producing numpy arrays based on 64
bit floats; in the future we could reduce the precision to 32 bit
floats: that would reduce by half the required disk space and the size
of the data transferred. But this is not decided yet, so we will stick
to 64 floats. 64 bit means 8 bytes per each float; the
question is: how many floats will the computation produce?
The answer is simply

  number of sites * number of IMT levels * number of realizations

assuming you want to save all the realizations of the logic tree.

However, both the engine and oq-lite can be tuned to avoid storing
the individual curves (i.e. the data for the individual logic
tree realizations). If you use that flag (set
`individual_curves=false` in the `job.ini` file) it is possible
to save a lot of space. In general, instead of the number
or realizations, it is enough to save an amount of data equal
to the size of the RlzsAssoc object, which is much smaller.
From such data it is possible to reconstruct all realizations.
For more information, you should read the [official documentation
about the RlzsAssoc object](
http://docs.openquake.org/oq-risklib/master/effective-realizations.html)

Just to be concrete, let me give some figures for the largest computation
that I know of, the full SHARE model for Europe. The calculation involves
126,044 sites, has 12 IMTs x 26 = 312 levels, 3200 realizations and 64
realization associations; the minimal disk space needed to store the
information about the realization associations is

   126,044 * 312 * 64 * 8 = 18.75 GB

In order to store all realizations, we should multiply by 3200 and not
by 64: this would require 50 times more space, i.e. 937.60 GB.

These figures make it clear why the oq-lite calculator is so much better
than the current engine calculator. Assuming you have fast disks (which we
have) you can expect a writing speed on a HDF5 file of 100 MB/s. That
means that we can write 18.75 GB in a bit more than 3 minutes. An insignificant
amount of time. The engine instead would require writing 937.60 GB of data
(the current engine has no table structure were to save the compact
representation of the hazard curves) on relation tables, at a speed at
least 100 times slower (the more the database if full, the slower is to
write on it, because of the checks on the indices, so it can be even worse
than that).

The 3 minutes of writing time could easily become something like
3 x 50 x 100 = 15,000 minutes, i.e. 10 days. Of course I cannot be sure
here since we never did such computation, we do not even have enough
disk space to attempt it. Instead the SHARE computation was done by
splitting per tectonic region type, by manually doing the optimization
that oq-lite is doing automatically and saving only 18.75 GB and not
937.60 GB. Then the 10 days becomes something like 5 hours, which is
reasonable. Still, 3 minutes is better!

Since SHARE is the upper limit of all computations, at least for the
current capabilities of the engine, it is safe to say that data storage
is never an issue when using an HDF5 file. Even saving all realizations
is possible in less than three hours (multiply the 3 minutes by 50),
assuming there is enough disk space. Thus the real bottleneck is
not the disk, is the data transfer. This will kill the calculator
well before the disk space becomes an issue. In a future post I
will explain how the amount of data transferred can be estimated
reliably. See you tomorrow!
