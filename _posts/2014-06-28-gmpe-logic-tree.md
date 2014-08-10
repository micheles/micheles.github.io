---
layout: post
title: The GMPE logic tree, how it works
---

One of the most complex areas in the engine is the management of logic
trees, both for the source model and for the GMPEs. Recently
I have been spending a lot of time in refactoring the code for
the GMPE logic tree. Substantial improvements were made, so
it is time to document what was done and the difference with the
past.

Let me start by explaining what I mean by GMPE logic tree.
When performing a hazard computation with the engine, the user
must provide a file, usually called `gmpe_logic_tree.xml`,
which specifies the Ground Motion Prediction Equations (GMPEs)
to use for each tectonic region type. For instance, suppose
we have a single source model with just two tectonic region
types A and B. Suppose that for the first tectonic region
type we have two GMPEs available, say A1 and A2, and that
for the second tectonic region
type we have three GMPEs available, say B1, B2 and B3.
Then the GMPE logic tree will have a total of 6 paths,
corresponding to the cross product of the possible
GMPEs:

 (A1, B1)
 (A1, B2)
 (A1, B3)
 (A2, B1)
 (A2, B2)
 (A2, B3)

For instance the first path means that the engine will perform
a computation with the GMPE A1 for tectonic region A and B1
for tectonic region B; the second path means that the engine will perform
a computation with the GMPE A1 for tectonic region A and B2
for tectonic region B; et cetera. The engine associates to each
path a so-called logic tree realization: the computation here
will generate 6 outputs, one for each realization.
Because of the combinatorics, the size of the logic tree can easily
grow; for instance, in the case of the SHARE Area Source model we have 7
different tectonic region types, each with several GMPEs:

Tectonic Region Type | Number of GMPEs 
---------------------|----------------
Subduction Deep | 2
Subduction Interface | 4
Volcanic | 1
Shield | 2
Subduction IntraSlab | 4
Stable Shallow Crust | 5
Active Shallow Crust | 4

A simple multiplication 2 * 4 * 1 * 2 * 4 * 5 * 4 = 1280 tells us that
this logic tree will have 1280 paths and thus the engine will have to generate
1280 realizations. In other words it will need to do a lot of work, 1280
times more work than for a single realization. This is why the SHARE
model could not be done with the engine directly; actually in the past it was
done by splitting the source model and doing one tectonic region type
at the time. If you split, the effort needed is 2 realizations for
Subduction Deep, 4 realizations for Subduction Interface, 1 realization
for Volcanic, 2 realizations for Shield, 4 realizations for
Subduction IntraSlab, 5 realizations for Stable Shallow Crust,
4 realizations for Active Shallow Crust, in total
2 + 4 + 1 + 2 + 4 + 5 + 4 = 22 realizations. Since 1280 / 22 = 58.18,
by splitting we can reduce the needed effort by around 60 times.

In May I realized that it was possible to implement the splitting
logic internally in the engine, i.e. to reduce the computation
from 1280 units of effort to just 22 units of effort: a *huge* gain.
So now the engine is ~60 times faster in computing the hazard curves
in the case of this logic tree; however it still saves on the database
all 1280 realizations. The saving part has not been improved at all
and so the post processing phase. This is why currently they are
the bottleneck for this kind of computations and it is why I am
working to change the database so that we can store only 22 units
of data instead of 1280 units of data. However, this will be long
and difficult, as always when changing a database.

But in a specific case we were lucky. I have found a way to get a *tremendous
speedup without touching the database at all*. The trick is that the
above multiplication assumes that all tectonic region types are
populated. But what if there are no sources for one of the tectonic
region types? Or there are sources, but such sources are beyond the
maximum distance for the sites of interest, so that they can be neglected?

Let's go back to the case with two tectonic region types, A and B,
and let's suppose that the tectonic region type B is not populated,
i.e. there are no sources for it. Then the paths (Ai, B1), (Ai, B2)
and (Ai, B3) will be indistinguishable: using the GMPE B1 or B2 or B3
will be the same, since there are no sources of tectonic region type B.
The engine will generate two triples of identical hazard curves,
thus wasting both computational power and disk space.

That's why *we changed the engine*. Now the engine does not generate
copies. In this case it will not generate 6 realizations but only 2
and the users will get only the 2 independent hazard curves.

The SHARE source model I described before was used by an OpenQuake
user who had no sources for the tectonic region types Shield and
Subduction Deep, each with two realizations. By excluding such
tectonic region types from the logic tree, we are left with
4 * 1 * 4 * 5 * 4 = 320 realizations instead of 1280
and 4 + 1 + 4 + 5 + 4 = 18 basic building blocks instead of 22.
That means that the original computation had a lot of copies
(320 independent hazard curves and 960 copies) that were bloating
the database without any reason and making everything slow.
But now everything is faster. In the case of our user, this
was the improvement:

time | before | after
-----|--------|------
calculation | 1.5h | 1h
saving | 2h |0.5h
postprocessing | 23.5h| 1h

Since we are saving 4 times less data, the saving time is 4 times
smaller, from 2 hours to just half a hour, and now it is lower than
the computation time, which is nice. But the most spectacular
improvement was in the post processing phase. In that phase
the engine is performing a lot of database queries, by computing
mean curves and quantiles. The performance there scales terribly
with the number of realizations, it is worse than quadratic: actually
having 4 times less realizations meant an improvement of nearly
24 times! We passed from 1 day to 1 hour! A huge success.

Of course, we are still not happy, because the database structure
is still inefficient, by storing 320 data units instead of 18 data units,
and because the post-processing could be done in memory without
any need to touch the database. So we still have a lot of room
from improvement. But in this case we were lucky, since
we got an enourmous speedup for free, without actually doing
any real work. The improvement on the logic tree library
was done to fix the bug of another user, you know.
Sometimes you get a free lunch ;-)
