---
layout: post
title: Analyzing large PSHA hazard calculations (3)
---

In a couple of previous posts I explained how to estimate the [disk
space occupation](/2015/06/16/large-psha-calculations/) and the [data
transfer](/2015/06/17/large-psha-calculations-2/) of a classical
calculation by using the `oq-lite info` command. Unfortunately, there
is no easy way to estimate in advance the memory occupation and the
runtime of a calculation. There is however a trick that can be
extremely useful: instead of running the full computation, you should
run a reduced version of it, measure the memory occupation and runtime
and extrapolate to the full computation.

How can you reduce the size of a calculation? The simplest
solution is to reduce the number of sites.
The size of the computation and the data transfer scale
linearly with the number of sites. So, if you have a
computation with 100,000 sites, you can reduce the
number of sites to say 10,000 and see how long it takes.
Then you will be able to make an educated guess on the figures
of the full computation, which will require 10 times more memory
and will have a data transfer 10 times bigger (assuming that the
logic tree does not change, which is not guaranteed).

How can you reduce the number of sites? By reducing the file
from which they are read. The sites can be read from a CSV
file containing longitudes and latitudes, or from a site model
XML file containing the site parameters, or from the exposure
XML file. `oq-lite` offers a `reduce` command which is able
to reduce each of theses files by performing a random sampling of
the sites. The syntax is

```bash
$ oq-lite reduce <fname> <reduction-factor>
```

where the file is usually called *sites.csv* or *site_model.xml* or
*exposure.xml* and the reduction factor is a number in range 0,..,1.
For instance

```bash
$ oq-lite reduce sites.csv 0.1
```

will sample the lines of the csv file and keep approximately one line over 10,
randomly. In other words, the reduction factor is the probability to
keep the line. If the file is in XML format, the reduction format
is the probability to keep the site.
`oq-lite` will reduce in place the file, but it will keep a
copy of the original file, with extension `.bak`, so that nothing
is lost. After you are satisfied with your test, so can just copy
the `.bak` file on the reduce file and perform the real analysis.

Reducing the number of sites is a very effective way of reducing
the size of a computation, but sometimes it does not work (in
particular when you have you are doing a site-specific analysis
and you have a single site) or it is not what you want (for instance
when you want to know if the required data transfer can be
managed by your technological stack). In such cases one does
not want to reduce the size of the computation nor the data
transfer: instead, one wants just to reduce the computation time,
to get some preliminary result shortly.

To achieve this goal, your best bet is to reduce the number
of sources. The `oq-lite reduce` command is also able to reduce
source model files; for instance you could run something like

```bash
$ oq-lite reduce source_model.xml 0.1
```

Be warned that the computation time is not necessarily linear with the
number of sources; if the sampling removes all the sources of a given
tectonic region type, the logic tree of the computation will be
reduce and the computation will become much faster. So the reduced
computation may not be a realistic representative of the full one.
But this is life: things are never easy. Still, it is always a good
idea, before starting a large analysis, to gain some experience
with reduced computations. Then you can discover early potential
problems and shortcomings: for instance, if you run out of memory
already with the reduced computation, it is an indication that
you should change strategy ever before attempting the full analysis.
