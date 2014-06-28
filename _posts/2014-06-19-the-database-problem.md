---
layout: post
title: The Database Problem
---


Necessary premise: *I love relational databases*. Before coming to GEM I
did spend 7 years of my life working with large, enterprise-level, relational
databases. I spent a lot of time in optimizing database queries,
designing relational tables, writing advanced views and stored procedures,
constraints and all that. I once implemented a partitioning project for 
PostgreSQL. Databases with over 100 tables and and tables with over
100 million records were normal to me. Even if I would not
call myself a database expert, certainly I am not a
beginner. And, as I said, I like the relational model and
I like to think relationally. So take everything I will say as
something coming from a database lover.

A couple of years ago I had my first job interview with GEM. During
the interview I was told about the engine, and about the fact that it
was using PostgreSQL as backend to store te results. At the time I was
pretty much surprised: I had never heard of using a relational
database to store numbers coming from a number crunching
application. It seemed like a bad idea. Then I got my job and I
started working on the engine. Then I discovered that the situation
was much worse than I could have imagined: the database was used not
only to store large arrays of floats, but for everything related to
the scientific logic.  The algorithms of the calculators were
implemented in the database.  Which meant that it was nearly
impossible to develop with the engine because, as you would do in a
web application, for every object you had to define a table, a Django
ORM class equivalent to that table, you had to write routines to
populate that table for usage in the tests, you had to implement data
validation code (both in the application and in the database, with
constraints and possibly stored procedure) et cetera. All things
that you would not need to do in a normal scientific application.
Actually, the engine felt
nothing like a scientific application and everything like an
enterprise application.

Within my first week of work with the engine I had
already identified all the major issues and found a solution,
which was essentially *the database has to go away from the scientific logic*.
It I could remove the database all the rest would have been comparatively
easy to solve. Unfortunately, removing the database was extremely
difficult and time consuming, since it meant rewriting nearly
all of the engine code. Basically I had three options:

1. Rewrite the engine from scratch. That would have been the best
option and the fastest to implement, but it was impossible to go that
way for non technical reasons. The fact is the engine had been just
rewritten from a previous implementation in Java. The management was
expecting to release the engine in six months, for them the project
was near completion and essentially done. It was impossible to say
"look, we have to start from scratch, *again*".

2. Rewrite the engine from within. That option meant rewriting the engine
slowly, piece after piece, while doing other things in the same time.
Essentially every time a performance problem came out on a specific
part of the engine (and the problem was *always* related to the database)
I could work at that part. The disadvantage of this option is that it
takes years. The advantage is that it is the safest way. At any moment
you always have a working implementation, you can release the product,
the users can play with it, they will find issues and bugs and then
you can progress slowly but surely towards your goal.

3. Do nothing and wait. This is actually a good option and it is the
one I adopted during my first months at GEM. When you are a new guy
this is essentially the best option you have since it gives you time
the to think of a plan of action. With time the situations may change,
old programmers may go away and you may even turn out to become the
official maintainer of the engine.

At the moment I am deep inside option 2. In particular this month I have
been rewriting the database structure of the event based calculator.
This is the most problematic calculator of all in the engine database.
After that I will have to rewrite the table structure of the classical
calculator, but that is comparatively much easier, so right now I am
focusing all of my attention on the event based. It is not the first
time I rewrite such table structure: the current structure comes from
a rewriting I put in place about one year ago. In may 2013 I spent a lot of time
working around the table structure which I had inherited to make it
more efficient and I was able to make [substantial improvements](
http://micheles.github.io/2013/06/12/the-story-of-Miriam-island-2/),
enough that the engine could be released in June. Not enough to satisfy
myself, tough. The table structure was a compromise: the minimal change
to the original structure that could solve the most dramatic performance
issues with the minimal effort. I simply did not have the time to
do anything better with the engine release the next month.
Now, however, I have more time and I am tring to do the right thing,
i.e. to design a sensible table structure, the most natural for the
calculator.

Once I have done that, I see two possible outcomes:

1. (optimistic) the performance both of hazard and risk improves by
a order of magnitude, we are all happy and we start addressing the next
issue

2. (realistic) the performance improves but not enough and we will have
to find a way to avoid the database.

One may wonder why I am spending so much time on the database refactoring
if I think that option 2 is more realistic. There are several reasons.

For once, we might be lucky and the performance improvement could be
so big to solve the issues our users are facing. If that it is the case,
then it could be good enough for the moment. Of course next year the
users will have bigger calculation and the database will become again
the bottleneck, since by design it cannot scale. If an user buy more
machines and grow her cluster, then the database will be stressed more
and more up to the point where no optimization will help. It is true
that PostgreSQL support clusters of databases, but at the moment
we are ignorant of that technology and we never did any experiment in
in that direction, so whereas in principle it could
help, we have no idea of how much. My gut
feeling is that it will not work and that we will have to change
approach completely, by not storing the data in a relation database,
but in a dedicated storage, such as [pytables]
(http://www.pytables.org/moin) or something like that.
Then we will have to change the risk calculators to read from the new
storage and that will be long and difficult. 

This is the major reason why I am sticking to the database: it is the
only option I have if I want the current risk calculators to keep
working. More than that: while working on the database refactoring I
am adding several QA tests that were missing. Those tests will become
invaluable in the future when we will have to go the hard way. Also,
the refactoring involves a better separation between the
scientific logic and the database logic. Ideally, one should
decouple the two concepts and make the database pluggable: i.e. by
changing a single configuration parameter I should be able to make the
engine to use the database or not.  Of course we are currently very
far from that goal: but that does not mean that it is not a worthy
goal or that it cannot be achieved. On the contrary, it is very
much achievable, only difficult and time consuming.  It may be taking
years, but we already progressing towards that goal and we already
made *huge* steps in that direction, even if we are still at the
beginning.

Notice that I do not plan to remove completely the database, even
in the long term. I want to remove the database from the number
crunching part of the engine, not from the rest. In particular the
database is extremely useful for logging/debugging purposes and to
store information about the computation. I have added myself several
tables for that purpose. For instance there is a table were we store
the running times and memory consumption for each operation performed
by the engine, for each task. A relational database is perfect to 
store and retrieve that kind of
information, and I do not plan to
remove such feature. So the database will stay. We had users that
asked if the engine could run without PostgreSQL; at the moment it can
not, however in the far future it is thinkable that the relational
information that I want to store could stay in a small embedded
database like SQLite. What must go away from the database are the big
numpy arrays, like hazard curves and ground motion
fields. Such structure should go into a dedicated storage. Then
we should be able to improve substantially the problem
we have when [retrieving large amount of data in the risk calculators]
(http://micheles.github.io/2013/05/17/the-story-of-Miriam-island).

Should the exposure data stay in PostgreSQL or not? This is a big
issue that has no definite answer for the moment. It is something I
have been thinking about. Currently we use the geospatial features of
PostGIS in the risk part; on the other hand, the usage of PostGIS in
the hazard part is minor and could be removed without a big
effort. The queries to read the locations of the assets from the
database and to associate them with the hazard sites are slow and have
been giving us a lot of headaches in the past.
The geospatial features are
more of an hassle than an advantage, performance-wise, because the database,
by construction, does not work well when stressed by hundreds of
workers performing simultaneous expensive queries. Luckily, I was able
to optimize them so that they are not the bottleneck at the moment,
but I am sure that they will become an issue again, because the users
will have larger exposures, or because the improvements in other parts
of the code will make them comparatively slower. My gut feeling is that soon or
later we will have to face that issue, and that the solution will be
to remove the geospatial queries altogether. At that time we may as
well throw away the dependency from PostGIS and therefore from
PostgreSQL.  But I see that in the very long term. We will have to
change the storage for all of the risk outputs and that would be a
major undertaking. So for the medium term we are stuck with the
database and there is no way around it.
