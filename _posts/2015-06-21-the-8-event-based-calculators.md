---
layout: post
title: The eightfold way to the event based calculator
---

As the readers of this blog already know, the event based calculator
is very complex. A summary of the status of the different versions
of it is needed. This post attempts to clarify the situation.

First of all, let me dispel the notion that there is a single event
based calculator: currently the engine contains at least *eight different
event based calculators* and, depending on how you count them, the
number could grow. Here I am referring to the current master, i.e. to
what will become version 1.5 of the OpenQuake engine. There are the
following event based calculators.

1. *The old rupture calculator.*
This is a calculator which is able to process a source model and
produce ruptures which are then stored in the database. This
calculator has been in the engine at least for a couple of
years. Originally (i.e. before 1.0) it was integrated in the event
based hazard calculator.

2. *The old GMFs and curves calculator.*
This is a calculator which is able to process the ruptures
produced by calculator #1 and to produce ground motion fields
and/or hazard curves. It has been in the engine for a couple
of years. Originally it was integrated in the event based hazard
calculator. This calculator could be split in two, since the
hazard curves functionality could be extracted.

3. *The old risk calculator.*
This is a calculator which is able to process the GMFs
produced by calculator #3 and to produce risk results. It has been in the
engine for several years, having experienced several refactorings to
simplify the database queries and to reduce the time spent to retrieve
the GMFs and the needed memory. Still, it performance it so poor
that a new revolutionary approach that does not need to read the
GMFs has been implemented in calculator #6.

4. *The new rupture calculator.*
It does the same job than calculator #1, but it stores the ruptures
in the file system instead than in the database and so it is
much faster, especially when the number of stochastic event set
is big.

5. *The new GMFs and curves calculator.*
It does the same job than calculator #2, but it stores the GMFs and
curves in the file system in HDF5 format instead than in the
database. It is much faster than the original calculator. As
input, it requires the ruptures produced by the calculator #4.

6. *The new event loss table calculator.*
It does much more than calculator #3, because it is able to compute
the ground motion fields on-the-fly (i.e. it has no need of calculator #5,
which is there only for debugging and analysis purposes) but
it produces much less outputs. At the moment it only computes
the event loss table; nevertheless, its feature set is growing. This
calculator does not need the database and saves the event loss table
in HDF5 format, so it is orders of magnitude faster than the original
calculator. Also, it requires orders of magnitude less memory.

7. *The experimental oq-lite risk calculator.*
This is a full featured replacement of calculator #3, but it is still
a work in progress and has known limitations. It is possible that in
the future it will be merged with calculator #6.

8. *The BCR event based calculator.*
This is an old calculator which has still no counterpart not relying
on the database. But such counterpart is scheduled to appear soon.

Once all the features of the original event based risk and BCR
calculator are ported to the new database-less system, it will become
possible to remove the old calculators and probably we will be down to
only 4 calculators (I say probably because new variations of the event
based calculator could appear). Unfortunately, for the moment the
situation is a bit of a mess.

Also, it should be noted that the event based calculators work in a
completely different way if sampling is enabled
(`number_of_logic_tree_paths > 0`): actually, it would be better to
consider such a case as a different calculator, since the performance
figures and the outputs are quite different. So the 8 event based calculators
should be counted as 16!
