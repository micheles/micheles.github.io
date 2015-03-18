---
layout: post
title: An introduction to OpenQuake Lite (oq-lite)
---

Since my first days at GEM we always had the idea, in some
unspecified future, of developing a "lite" version of the engine. This
version was meant to be run on regular consumer machines, including
Windows laptops. In order to reach that goal it was important to remove
some Unix-only dependencies and to introduce an OS-agnostic installation
procedure. A reduction in features and in performance was considered
acceptable: the goal of oq-lite was to make it possible to run
simple computation on a laptop and then, if the user wanted to
run something serious, she could have sent the computation on a big
server or on a cluster, *by using exactly the same input files*.
In other words, oq-lite was meant from the beginning as a tool
for prototyping hazard and risk calculations.

After two years and half of experience, we realized that `oq-lite` could
be much more than that. Now the idea is that `oq-lite` should
be a library on top of which the full engine is built. Being a library
means that

1. third party organizations can take `oq-lite` and build their own
   engine on top of it, in a way which is infinitely easier and
   more efficient than using the current engine;
2. anybody can easily write a custom user interface for oq-lite, or
   even more than one user interface

The `oq-lite` library has a lot less dependencies than the real engine:

- oq-lite does not depend on celery
- oq-lite does not depend on rabbitmq
- oq-lite does not depend on Django
- oq-lite does not depend on Postgres

Moreover, it has a lot of other advantages with respect to the full engine:

- oq-lite is configuration-less
- oq-lite is faster than the engine for small computations
- oq-lite is focused on the scientific algorithms and contains an
  extension facility so that it is easy to implement custom
  calculators, whereas it is very difficult to do so in the full engine
- oq-lite is easy to port to multiple operating systems; at the moment
  we support both Linux and MacOS and in principle it is easy to
  support Windows too

For a point of view of a developer, the most important thing about
`oq-lite` is that *it does not depend on the database*: that means
that refactoring the full engine to use oq-lite as a library
forces a separation of concerns between the database-related part of the engine
and the database-independent part. This separation was much needed,
I have worked more than two years to achieve that goal and now we
are close to finally get there (perhaps only one other year of work!).

This is important because all of the performance and scaling issues
we ever had are essentially related to the database; incidentally,
this is hardly surprising, but we have inherited this terrible
design decision from the past and we had to cope with it.

At the moment all the hazard calculators except the disaggregation one
have been ported to `oq-lite`, so an user can reproduce hazard calculations
on her laptop without having to install postgres/rabbitmq/celery/django.
The usage as a library is quite trivial; if you have a zip file with
the input files you can just run from the python interpreter the
following command:

>>> from openquake.commonlib.commands import run
>>> run.run('input_files.zip')

For convenience, the `oq-lite` library comes with a command-line tool
called `oq-lite` which is able to process zip archives:

 `$ oq-lite run input_files.zip`

`oq-lite` is able to run zip files, but also .ini configuration files:

 `$ oq-lite run job.ini`

The format *is the same* used by the full engine, because internally the
full engine is already using `oq-lite` to parse the input files and to
run the calculation. Also the input validation is shared, so if a file
is valid for `oq-lite` is also valid for the full engine and viceversa.

Currently there is still some (little) amount of duplication between
`oq-lite` and the full engine, but this only temporary: we have been
removing code from the engine for over one year and we will keep doing
so until there is not a single line of duplication between `oq-lite` and
the engine.

For instance, at the moment the engine event based calculator
is just a thin wrapper over the `oq-lite` event based calculator.
That means that by construction the numbers you gets from the full
engine are exactly the same that you get from the lite engine,
since you are really doing the same calls. That means that now
it is much easier to debug problem in the full engine, since
you can see what happens in the lite version of the engine to
understand where the problem is.

It is important to point out that the test suite of the full engine is
shared with the test suite of `oq-lite`: fully supported calculators
have the same level of reliability and produces exactly the same
outputs than the full engine.

`oq-lite` has also some introspection facilities and some plotting facilities
which are missing in the full engine; already now it has more features
than the full engine, at least for the supported calculators.

The weak spot of `oq-lite` is the coverage of the risk calculators:
except for the scenario damage calculator, they have not been ported yet.
Once they will be fully ported (in one year time frame, so do not keep
your breath) then `oq-lite` will become much better than the current
engine and at that point all of the database-related performance issues
we have will disappear. Unfortunately, there is still a lot of work
to do before we can reach that goal...
