---
layout: post
title: Database Migrations
---

The current version of OpenQuake (OpenQuake 1.0) does not support database
migrations. That means than an user upgrading to a newer version of OpenQuake
must create a new database from scratch and cannot use the results in the
old database. Actually the current upgrade procedure *destroys* the
database. This is clearly far from ideal.

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

Cutting edge users, using GitHub or the nightly builds, will be able
to use the new mechanism even before the official release of OpenQuake
2.0. They will need to upgrade all of the OpenQuake-related
repositories and run the command `$ openquake --upgrade-db`.
When some change to the database enters in the code base,
users keeping updated their repositories will see an error like this
when running a new computation :

  Your database is not updated. You can update it by running
  `$ openquake --upgrade-db`

By giving this command their database will be automatically updated
without losing data and then they will be able to run their computation.

That in an *ideal* world. In the real world something may go wrong.
In particular the migration may fail. In that case the upgrade mechanism
will perform a rollback and no changes to the database will be performed.
This is a safety net guaranteeing that nothing bad will happen.
The user will go back to a versions that worked, and will tell
us about the problem she had, so that we can help with a solution
to make the migration possible. We will also add a command

  `$ openquake --version-db`

which will print out the current version of the user database.

There is a potential issues with migrations. They may be *slow*. If an
user has a database with millions of rows, and the migrations has to
touch all of them, it may takes hours or even days. In such cases we
will warn the users. It is safe to kill a migration that it is taking
too much time: the database will revert to the previous situation. In
such cases is probably best to proceed manually: for instance a large
table can be truncated, or even the full database can be destroyed and
recreated. Actually it may be (much) faster to regenerate the results
of a computation than to perform a migration.

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

openquake --what-if-I-upgrade
---------------------------------------

To help the users wondering if they should migrate to the newest version
of OpenQuake or not, a command-line switch ``--what-if-I-upgrade``
will be added to the ``openquake`` command: when invoked, this
command will look at the [directory containing the upgrade scripts]
(https://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrades) on GitHub and figure out which migrations are missing in your version
of OpenQuake. The name of the upgrade scripts follow the following
convention:

`[four-digit-version-number][optional-flag]-[name].[extension]`

where the extension can be `.sql` or `.py` and the `optional-flag` can
be `-danger` or `-slow`; the flag `-danger` identifies the
scripts that can potentially destroy data, whereas the flag `-slow`
identifies the scripts that can potentially be slow. When running
the `openquake --what-if-I-upgrade` command, the user will get
something like that:

```
Your database is at version 0007. If you upgrade to the latest master, you
will arrive at version 00014.
Please note that the following scripts could be slow:

https://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrade/0011-slow-set-rupture_id-not-null.sql
...

Please note that the following scripts are potentially dangerous and could destroy your data:

https://github.com/gem/oq-engine/tree/master/openquake/engine/db/schema/upgrade/0012-danger-drop-gmf_data.sql
...

Click on the links if you want to know what exactly the scripts are doing.
Even slow script can be fast if your database is small or they touch tables
which are empty; even dangerous scripts are fine if they touch empty tables
or data you are not interested in.
```

If there are no scripts marked `-danger`, you can safely upgrade; it there
are scripts marked `-slow` you may try to migrate anyway; if you see that
the migration takes too much time, you can kill it, empty the table
that it is making the migration slow, and restart it. If there are scripts
marked `-danger` you should look at their content on GitHub: in a
comment there will an explanation about what exactly that script is doing.
In practice, you want to upgrade anyway, even if the script is marked
`-danger`, but before upgrading you may want to save some of the data
that would be destroyed.

In any case, if you have two machines with OpenQuake
installed, you may want to upgrade only one machine, perform a
computation with the new version and compare the results with the
old version, before deciding to migrate. Please take in account
that even if there are no database migrations a new release of
OpenQuake can contain different algorithms and/or bug fixes
and so can produce different numbers than the old release.
