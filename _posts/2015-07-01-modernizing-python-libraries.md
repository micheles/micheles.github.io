---
layout: post
title: Modernizing Python libraries
---

The last couple of years I have been sleeping and in the meanwhile
everything changed in the Python world. 

Actually, I was not sleeping, but fighting with the engine
database. Now that the fight is won - at least in my mind, in reality
it will take at least six other months to be finished - I have started
to wake up and I have begun to consider issues other than the database.
Among them, there is the question of the migration to Python 3.
This has always been low priority for me and it still is; however,
soon or later we will have to address the issue, because
some users will start using Python 3 and will ask for support.
After all, some Python distribution are starting to ship Python 3
as default and [Ubuntu 16.04 may be amongst them](
https://www.phoronix.com/scan.php?page=news_item&px=Ubuntu-16.04-Python-Plans)

The good thing is that during the two years of my sleep everything changed
for what concerns Python 2->3 strategy plans: and it changed for the better.

*Nowadays, there is no need to migrate to Python 3 anymore, if by
migration we mean abandoning Python 2: on the contrary, we can
still use Python 2 and have the same code run on Python 3 too!*

This is a *complete revolution* compared to the times of the [2to3
migration tool](https://docs.python.org/2/library/2to3.html).
Years ago, the suggested strategy was to develop with Python 2
and have an automatic tool convert the code base to Python 3.
That meant having an intermediate build step during installation
or having to ship different packages, one for Python 2 and one
from Python 3, obtained from the first one. This is of course
inconvenient, especially for large code bases (you have to rebuild
everything for each code change); moreover, if the conversion
cannot be fully automated (as it happens) it means that at
each modification one has to carefully check that the generated
Python 3 code is still good.

Having a single code base is clearly a superior solution, because it
avoids any intermediate (and fragile) step; moreover, it allows to procede
incrementally. Consider for instance the situation of the GEM
libraries, i.e. respectively:

- openquake.baselib
- openquake.hazardlib
- openquake.commonlib
- openquake.risklib
- openquake.engine
- openquake.server
- HMTK, RMTK, ...

If the Python 2 codebase is not abandoned, but just modernized, so
that the same library can also work with Python 3, the migration can
be done incrementally. For instance today I have modernized baselib,
without any ill effect on all the rest of stack; tomorrow I could
modernize hazardlib, allowing people to use Python 3 with it, without
any need to touch the other libraries. In particular I want to make
oq-lite as portable as possible: it already run on Windows, and I can
also port it on Python 3 with a relatively small effort. It is enough
to port hazardlib and commonlib; risklib is already compatible with
Python 3 (out of the box: I did not have to change anything!).

Thanks to the support in Python 2.7 and Python 3.3, plus
the existence of compatibility layers like [six](http://pythonhosted.org/six/)
and [future](http://python-future.org/index.html) having an unique codebase
is no more a pipe dream. The work required to modernize
a project like oq-lite, which has to do with scientific computing and it is
essentially free from unicode-related issues, is modest, actually much
less than I was expecting. There are already automatic tools doing most
of the job, like *python-modernize* and *futurize*: while not perfect,
they seems to work well enough with our usage of Python.

And there is another *huge* improvement: the modernization needs to be
done *only once*: having done it, it is enough to add a check so that
every pull request that tries to use Python 2-only idioms is rejected
up front. This guarantees that the code base stay clean and Python
3-compatible.

For the moment we do not plan to migrate to Python 3, so it is enough
to modernize our basic libraries (what is needed for oq-lite and
nothing more) and to check for Python 3 syntactic correctness: that
means that it is enough to run `python3 -m py_compile` on all the modules.
That will force our contributors to be Python 3-aware, and will be
useful as a training exercise. 

In the future, when we will consider supporting Python 3 for real, we
will need to install the full Python 3 stack (fortunately it seems
that all the third party libraries that we need have been already
ported) and set an instance of Jenkins running the tests with Python
3. Then we will discover the subtle things, we will likely fix a few
bugs and finally we will be ready to ship an oq-lite version working
with Python 3. This could be done in the second half of 2016, after
the migration to Ubuntu 14.04 and after we discontinue the support for
Ubuntu 12.04. At that time we will consider what
to do with the engine. For that time the engine, as it is now, may
have evaporated: maybe it will just be a thin layer over oq-lite. Then
the porting of the engine will be trivial too. If the engine will not
have evaporated, we will think about what to do: porting it anyway, or
just wait more time for its evaporation, or even not doing anything, since
other things may have a bigger priority. The same thing can be said for
libraries like the Hazard Modeler Toolkit and the Risk Modeler
Toolkit: they may be ported to Python 3 or they may be not ported: in
any case, everything will keep working with Python 2.7 as it is now.

This is a great, great thing. It reduces the stress of a potentially
difficult and dangerous migration to a minor annoyance if not all
libraries can be migrated. With the old 2to3 approach, one had to
migrate all or nothing. Now we can migrate a minimum and still be of
service to the users. For instance if we just modernize hazardlib, we
will still be of service to all users using only hazardlib and wanting to
use Python 3.

My plan for the moment is to follow the suggestions of [Amin Ronacher](
http://lucumr.pocoo.org/2013/5/21/porting-to-python-3-redux/) and to
write a custom compatibility wrapper for the features that we need
at GEM. I will see how well this will work only when trying to fix
the tests. I have already seen that the tests of hazardlib do not
run out of the box, even if the syntax is Python 3 valid, but that's normal,
since there have been changes in the semantic. Since I did not write
hazardlib, fixing broken tests may not be the easiest things in the
world, but that's life. We will see when we will reach that point.
