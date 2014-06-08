---
layout: page
title: The Engine Repositories
---


To an user the OpenQuake Engine is a command-line tool to perform
hazard and risk calculation; to me, as a developer, the engine is
a set of libraries that can be used as building blocks to build
the features we want to add.

Currently the engine code base is split among 5 different repositories:

- [oq-hazardlib](https://github.com/gem/oq-hazardlib)
- [oq-nrmllib](https://github.com/gem/oq-nrmllib)
- [oq-risklib](https://github.com/gem/oq-risklib)
- [oq-commonlib](https://github.com/gem/oq-commonlib)
- [oq-engine](https://github.com/gem/oq-engine)

[hazardlib](https://github.com/gem/oq-hazardlib) is the real heart
of the engine, *hazardlib is where the hazard science is*. It has been there
from the very beginning, and it is also the most stable, most tested
and best working part the engine. It is the part that required less
maintenance (I hardly touched it since I started working with
the engine) and had very few bugs. It also makes the scientists
quite happy, it is intended for them, and they are the ones that
mostly develop with it. The typical use case is writing
a new Ground Motion Prediction Equation (GMPE) or modify one
which is already there. There is also a plugin mechanism so
that anybody can write his own GMPE, put it in a module
in the right directory, and `hazardlib` and the engine
will automatically recognize it.

In short, `hazardlib` *is good*.

[nrmllib](https://github.com/gem/oq-nrmllib) is also one of the oldest
components of the engine. It has been there forever and its goal is to
provide convenient utilities to read and write XML files in a custom
format called NRML (Natural Hazard's Risk Markup
Language). Essentially all of the input/output of the engine, with
very minor exceptions, is passing through the NRML format. This is not
necessarily a good thing, especially for what concerns the output. XML
is one of the most verbose formats there is, and it is certainly not a
good fit when exporting millions of floating point numbers, which is
one of the thing that the engine does.  Moreover it forces the users
to write their own custom parsers to read the data and extract the
information they need. There have been talk to support different
formats (i.e. .csv and binary formats such as
[HDF5](http://www.hdfgroup.org/HDF5/)) for a long time and probably
this will happen in some future, but it is impossible to say when
right now.

`nrmllib` *is bad* for a number of reasons that would require a long
blog post to discuss. It is essentially a legacy of the past. It is
still there since luckily we don't change our XML formats too often
and so it is tolerable to keep the status quo. But I personally would
like to kill `nrmllib` and move its important functionalities in the
other repositories, by throwing away 80% of its contents. Especially
bad is the dependency from `python-lxml` which has been extremely
brittle and has given us *a lot* of maintenance issues: it seems that
each new version of `python-lxml` breaks `nrmllib`.

[oq-risklib](https://github.com/gem/oq-risklib) is a relatively recent
repository (it was started less than two years ago) but the
functionality it contains has been in the engine for years. It is
an example of the trend which we have been following in GEM in
the last few years: moving stuff away from the engine and putting it
into separate repositories. The goal is to simplify the engine,
which in the end should just be a bit of glue over the underlying
libraries. At the moment, instead, the engine contains still a
lot of logic and it is much more complex that it needs to be.
`risklib` is considerably more high level and compact that
other parts of the engine; it works well, required few changes
and had very few bugs. It is intended to be the equivalent of
`hazardlib` for risk, but for the moment it has been used much
less.

In short, `risklib` *is good*.

[oq-commonlib](https://github.com/gem/oq-commonlib) is the newest
repository in the engine code base. The work on it started several
months ago but it has become a dependency of the engine only one
month ago, when the logic tree module has been moved into it.
Being so new, `commonlib` cannot be considered stable, but it is
a very promising piece of the engine: with time more and more
functionality will go into it and it will become an ever more
essential component. I have a plan to advertise `commonlib` as
much as possible, because it is intended for direct use by
the scientists and as a common base on which to develop desktop
tools without requiring a full installation of the engine.

In short, `commonlib` *is good*.

[oq-engine](https://github.com/gem/oq-engine) is the repository where
the code specific to the engine is kept. It is by far the largest
repositories of all and the one where most of the effort went. It is
also the one with the most contributors. `hazardlib`, `risklib` and to
a lesser extend `commonlib`, had each one major contributor, although
a different one for each library, and so they exhibit some internal
consistency, even if there is no strong inter-library consistency. The
engine, on the contrary, never had a major contributor or architect:
historically the CTO changed quite often at the beginning of the
development, so that the architecture of the engine has been
schizophrenic at best. It started as the brainchild of [noSQL]
(http://en.wikipedia.org/wiki/NoSQL)
enthusiasts, with Redis as its unique database; then it went into the
hands of PostgreSQL lovers, so that everything (even too much) went into
the database; however the previous design was not entirely removed and the two
approaches kept living together. At the beginning it was not clear if
the engine had to provide a web interface, so was built on top of a web
framework ([Django](https://www.djangoproject.com/)) even if it turned out
later on that the web
interface of the engine would have been a different application, the
[OpenQuake Platform](http://www.globalquakemodel.org/openquake/about/platform/).
So now we have a number crunching tool implemented with the
language of a web framework, not the best of the worlds. At some point
there where three different mechanism to perform concurrent
computations, without any technical reason for that, just because of
history.  Also, the team of developers was split between Zurich and
Pavia, with serious communication issues, so that the hazard part was
build without knowing the needs of the risk part, and the risk part
was build by following the example of the hazard part, even when
following that example was a bad idea. I could go on for hours,
but let me keep it short here. The essential point is that now the
engine is developed primarily by myself, and that I do have both a
clear picture of where the engine must be going and also the ability
to implement the required changes. In the last few months a lots of
the historical baggage has been removed: there is no Redis database
anymore, there is a single distribution mechanism used everywhere, the
database structure is more rationale than it was and we are going in
the direction of decoupling the engine from the database and move as
much as possible of the logic inside `commonlib`, so that it can be
used in other applications as well.

In short, *the engine is not good yet, but it is much better than it
used to be and it keeps improving*.
