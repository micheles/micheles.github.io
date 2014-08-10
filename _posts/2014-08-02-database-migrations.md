---
layout: post
title: Database Migrations
---

The current version of OpenQuake (OpenQuake 1.0) does not support database
migrations. That means than an user upgrading to a newer version of OpenQuake
must create a new database from scratch and cannot use the results in the
old database. This is clearly far from ideal.

Actually, internally at GEM we use a migration mechanism, so that
we may upgrade our database to work with newer versions of OpenQuake
without losing any data. Unfortunately the migration mechanism
is manual and requires expert kwnoledge to be used (i.e. there is
no protection against errors).

The good news is that we are working at implementing a fully automatic
migration mechanism, which will become available in OpenQuake 2.0.
There will be no support for migrating from Openquake 1.0 to 2.0, i.e.
users will not be able to use data coming from an OpenQuake 1.0
database. However, users with OpenQuake 2.0 will be able to upgrade to
later versions (2.1, 2.2, etc) without losing data.
The migration will happen automatically, at installation time.

Cutting edge users, using GitHub, will be able to use the new mechanism
even before the official release of OpenQuake 2.0. They will need
to upgrade all of the OpenQuake-related repositories and to recreate
the database. After that, the engine will just work. If some
change to the database will happen in the future, and the users keep
updated their repositories, when running a new computation
they will see an error like this:

  Your database is not updated. You can update it by running
  `$ openquake --upgrade-db`

By giving this command their database will be automatically updated
without losing data and then they will be able to run their computation.

That in an *ideal* world. In the real world something may go wrong.
In particular the migration may fail. In that case the upgrade mechanism
will perform a rollback and no changes to the database will be performed.
This is a safety net guaranteeing that nothing bad will happen.
The user will go back with Git to a versions that worked, and will tell
us about the problem she had, so that we can help with a solution
to make the migration possible.

For users relying on the debian packages, the migration will happen at
installation time. In case of error the installation will fail
with an error message and the user will have the option to go back
to the previous version of OpenQuake. The database will not be changed.

There is a potential issues with migrations. They may be *slow*. If an
user has a database with millions of rows, and the migrations has to touch
all of them, it may takes hours or even days. In such cases we will
warn the users in the release notes. It is safe to kill a migration
that it is taking too much time: the database will revert to the
previous situation. In such cases is probably best to proceed
manually: for instance a large table can be truncated, or even
the full database can be destroyed and recreated. Actually it may be
(much) faster to regenerate the results of a computation than to perform
a migration.

Now consider the following use case. An user performs a hazard
calculation and some risk calculations on top of it. Then she upgrades
to a newer version of OpenQuake and she wants to recomputed the risk
by using the old hazard data. Is that possible?

In general the answer is no. We cannot guarantee the consistency of using
old hazard results to compute the risk with a new version of OpenQuake.
Our tests and checks are meant to guarentee the consistency between
hazard and risk *for the same version* of OpenQuake. We cannot simply
support consistency with the past, for several reasons. For instance
suppose that there was a change in the hazard between version 2.1 and 2.2,
because a bug was discovered: in that case the hazard results obtained
with version 2.1 are wrong. The migration procedure will update the database
so that the data will not be lost, but it will not make it magically
correct. In that case the user will have to repeat the hazard calculation
using version 2.2 in order to get hazard data she can trust.
The same happens in case of changes of logic: for instance in version 2.2
we could change the hazard algorithms, so that the numbers will be slightly
different than before. Then, it order to be consistent, one must
repeat the hazard calculation with the new version of OpenQuake.

The migration procedure is particularly useful for people using
OpenQuake from GitHub. Since there is work on the engine every day,
there is essentially a new version every day. However versions
breaking compatibility between hazard and risk are rare (say 2-3 per
year): so it is normally safe to use hazard results from an old
version to compute risk results with a new version. This is totally
different from the situation of people using the official packages:
since there is release every year or so, it is basically sure that
such users will have to recompute their hazard.

It is GEM responsibility to warn the users when there is a
compatibility breakings; if an upgrade involves one of such breakings a
warning will be printed during the upgrade procedure and the user will
have the option to abort the upgrade. It must be stressed that errors
happen: so even if we think that an upgrade is compatible with the
past and our tests tell us so, we may be wrong. After all our tests
cannot cover all of the possible use cases, and the user data may be
quite different from the test data we have.  So it is always best to
make sure that both hazard and risk are computed with the same version
of OpenQuake.
