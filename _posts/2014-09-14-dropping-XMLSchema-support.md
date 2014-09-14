---
layout: post
title: Supporting the XMLSchema for NRML format, a wasted effort?
---

Currently all of the input/output of the OpenQuake engine is mediated
by XML files in a custom format called NRML ([Natural Hazard Risk
Markup Language](https://github.com/gem/oq-nrmllib)). The only
relevant exception is the `job.ini` configuration file.

In the past we had a lot of discussion about supporting different
formats, since XML is not the ideal format for all kind
of data; in particular for outputs which huge matrices of number
a binary format such as [HDF5](https://github.com/gem/oq-nrmllib)
could be a better choice. However today I am not discussing
alternative formats: I want to stick to NRML, but I want to
raise some concerns about its validation.

The interesting thing about XML is that there are several technologies to
validate it: at GEM we are using the
[XMLSchema](http://www.w3.org/XML/Schema) standard. In practice, in order to
validate a NRML file, one must define a specification for it in terms
of XML files following the XMLSchema format. Let's call them the
`.xsd` files, from the name of their extension. Then there are tools able to
validate the NRML file according to the given `.xsd` files. In
particular, you can find the `.xsd` [files specifying NRML on
GitHub](https://github.com/gem/oq-nrmllib/blob/master/openquake/nrmllib/schema/nrml.xsd). The specification is rather complex since it involves dozens of files;
moreover it relies on the [GML
standard](http://www.opengeospatial.org/standards/gml) which has its
own validation. However, this is not necessarily a problem; the
problem is that *the XMLSchema validation of NRML is insufficient*.

This is in my view a *very* serious problem: it is extremely easy
to write down NRML files which are valid according to the schema
and which are actually *invalid* according to the engine. So the whole
point of the XMLSchema is lost. An user writing a well formed NRML
file may find it rejected from the engine, possibly in the middle
of a computation and possibly with an ugly error message.

This is bad. What we need to do is to provide the users with a
validation tool which:

1. it is using the same identical validation that the engine does,
   not a partial and insufficient version of it
2. it is easy to install and does not require the full stack of the
   engine

Both requirements are not easy to satisfy, however after several
months of effort (we started over one year ago with the project on the
desktop tools) we are finally in a position where the tool is nearly
ready. The validation in the engine has been completely rewritten from
scratch andt now it does not rely on Django, nor on the engine
database, but only on functionalities coming from commonlib, that can
be easily installed, since its dependencies are the same of hazardlib
and risklib. Moreover the procedure to convert from NRML sources to
hazardlib objects has been rewritten and now it is

1. more reliable (i.e. with better and earlier error messages)
2. faster (up to two times when converting large input models)
3. more memory efficient (before the XMLSchema validation was keeping
   the whole XML file in memory, now the validation is done incrementally)
4. the code base has shrink by several thousand lines of code

So everything is good and there are no disadvantages, and that is
possible only because *a lot* of good work went into it.

Being this the current situation, one may wonder what it is the point
of maintaining the XMLSchema. The new validation mechanism bypasses it
entirely.  In order to enforce the validation needed by hazardlib and
risklib it *has* to bypass it. Even before we had two steps of
validation, one in the XMLSchema and one in the engine, but the one in
the engine was not reliable, with bad error messages, and so we had to
relay on the existence of the previous XMLSchema validation. Now the
XMLSchema validation is useless and it is not performed by the engine;
actually, to be accurate, here I am speaking about the hazard
sources, since the risk inputs are still using the old system until
the old parsers/converters are replace by the new ones.

Maintaining the XMLSchema has a *big* cost: while reading `.xsd` files
is not so bad, writing them is another matter: our experience from
the past tells us that even small changes usually required days of
effort, considering also the time to write parsers/writers/converters
and tests. So I say that we should consider dropping the
support for the XMLSchema, and having instead an official GEM
validator for all of our NRML files. This is not urgent, and we could
keep the existing system for a transition period, by replacing the old
system with the new system one piece at the time.

Of course, we would lose a formal specification of NRML, which would
be replaced by an operative definition depending on the concrete
implementation of a validation tool, but sometimes practicality beats
purity. Moreover, there is the existence of a few concrete
shortcomings to be considered. Unfortunately, to support XMLSchema
validation is a big issue in the Python world.  I only know of two
enterprise-level libraries that support it: lxml and the XML library
of PyQt. They both rely on underlying C libraries. My experience is
that:

1. PyQt validation rejects our NRML files saying that they are invalid
   even if they are valid according to third party tools such as xmllint.
   At least for the version of PyQt that I tried a few months ago.

2. lxml is *extremely* dependent on the version used. Our experience
   is that every time you change version some thing breaks. Even for
   minor versions. We were bitten by problems at least 4 or 5 times
   in the past: we found several bugs in specific versions of lxml,
   we had to change our parsers at least once to work around some
   issue, and currently the validation of some of our files with the
   version of lxml that ships with Ubuntu 14.04 segfaults.

In other words, it is a big pain to maintain the support for validation.
We have also the experience of some of our users wanting to install
the engine on a different system (Debian instead of Ubuntu) and giving
up essentially just because of issues with the installation of a working
version of lxml. It seems that the XMLSchema validation is
much less tested than the rest of the codebase of lxml, so even versions which
are able to parse NRML files flawlessly choke on their validation.


Appendix: examples of insufficiently validated NRML files
-----------------------------------------------------------------

I could show several examples, but since I don't want write a bible
about NRML validation, I will give a single example:
[discrete fragility functions](https://github.com/gem/oq-nrmllib/blob/master/examples/fragm_d.xml).
If you click on the link you will see immediatly why this kind of files
cannot be validated by an XMLSchema. The limit states are not fixed:
a validator must read them from the node `<limitStates>` and check
that below there are fragility functions (`<ffd>` nodes) for each and
one of them. The intensity measure levels are not fixed: for each
fragility function set (`<ffs>` node) a validator must extract the IMLs
and make sure that the number of poes for each underlying fragility
function is the same as the number of the given IMLs. Moreover the
IMLs must be sorted and without duplicates. For
[vulnerability functions](https://github.com/gem/oq-nrmllib/blob/master/examples/vulnerability-model-discrete.xml) the validations are even more complex.
Since they cannot be encoded statically in the `.xsd` schema, currently
they are performed in risklib. That means that an invalid file (for instance
with the wrong number of poes) passes the
XMLSchema validation and the problem is discovered only in the `pre_execute`
phase of the engine, with an ugly error message, for instance something
like:

```python
  File "/usr/lib/python2.7/dist-packages/scipy/interpolate/interpolate.py", line 278, in __init__
    raise ValueError("x and y arrays must be equal in length along "
ValueError: x and y arrays must be equal in length along interpolation axis.
```

Notice that the error does not say the name of the invalid file, nor
the line number where the invalid node is; in this case I have removed
one poe from a `ffd` node, and it is certainly a nontrivial debugging
job to find out where the problem is, considering that the fragility
functions files can contains dozens or hundreds of nodes. And there
is no way to perform this kind of validation at the XMLSchema level.
