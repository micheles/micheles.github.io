---
layout: post
title: Analyzing large PSHA hazard calculations (2)
---

In a [previous post](/2015/06/16/large-psha-calculations) I explained
how the size of a computation (in terms of disk space occupation) can
be computed. However, there is another measure which is critical when
estimating the feasibility of a calculation: the amount of data
transferred between the master and the worker nodes and back.

This number is of paramount importance, especially in the engine,
because the technology we use to transfer the data (i.e. rabbitmq)
is not able to cope with big data. Any computation with a
data transfer exceeding 10 GB is at risk of failure in the rabbitmq side.
Even in the best case, it will be very slow.

Here I will document how to estimate the required data transfer with
oq-lite.  It should be noted that the amount of data transferred in a
calculation is subject to change, because we are always working to
improve the calculators in order to reduce it. I will describe the
figures for the current classical PSHA calculator, which apply both to
the engine and to oq-lite. The data transfer depends heavily on the
number of tasks that will be generated: the more tasks are generated,
the bigger the data transfer. The number of tasks is controlled by the
parameter `concurrent_tasks`, which can be specified in the `job.ini`
file (this is a new feature introduced yesterday; before it has to be
specified in the openquake.cfg file, that required root permissions to
be edited).  If the parameter is not specified, it is considered to be
equal to 8 times the number of cores in the controller machine. This
is a value which is fine for our cluster, but not in general. You should
always specify a `concurrent_tasks` parameter, and it should be large
enough that all of your cores are used. 

To see an example where the parameter is specified, you can have a
look at the OpenQuake demo *AreaSourceClassicalPSHA*, where the parameter is
set to 10. This means that both oq-lite and the engine will try to
generate a number of tasks around 10. Actually
`concurrent_tasks` is just a *hint*, internally the code will produce
a number of tasks close but not necessarily equal to it. oq-lite
provides an `info -d` option to know how many tasks will be generated
without running the calculation. On my laptop I get :

```bash
$ oq-lite info -d demos/AreaSourceClassicalPSHA/job.ini
Number of tasks to be generated: 10
Estimated data to send forward: 577.91 KB
Estimated data to send back: 31.74 MB
```

The `-d` option (aka `--datatransfer`) also estimates the data transfer
from the master to the slaves and back; the estimate is not perfect,
the real numbers will be a bit bigger, but not much for large
computations. Also notice that on another machine you could get
slightly different numbers, depending on your version of Python and
its libraries and the operating system. Just to give you an idea,
if I run the demo on my laptop, from the log file I get

```
INFO:root:Sent 581.99 KB of data
INFO:root:Received 31.75 MB of data
```

i.e. the estimates are pretty good. If you are curious about how the
numbers are computed, you should [look at the code]
(https://github.com/gem/oq-risklib/blob/master/openquake/commonlib/commands/info.py). Here I will simply notice that the dependency on the number of tasks is
pretty significant; for instance, if I increase the parameter `concurrent_tasks`
to 20, I get

```bash
$ oq-lite info -d demos/AreaSourceClassicalPSHA/job.ini
Number of tasks to be generated: 19
Estimated data to send forward: 1.04 MB
Estimated data to send back: 60.31 MB
```

NB: the `oq-lite info -d` can be rather slow if the computation is very
large. It will however be much faster than the real computation.
If `oq-lite info -d` is so slow that it does not run to completion in a
reasonable amount of time (say 1-2 hours) then it means that you should
start thinking about reducing your computation. You will have little hope
of running it as it is.

In the case of the SHARE model on our cluster running
`oq-lite info -d` takes 1 hour and 3.5 GB of RAM(!), with the following result:

```
Number of tasks to be generated: 266
Estimated data to send forward: 1.86 GB
Estimated data to send back: 317.32 GB
```

The limiting factor is the sheer size of the data to be sent back,
over 300 GB. This is why a calculation of this size can only be
done with a tiling calculator, which I will discuss in a future
post.
