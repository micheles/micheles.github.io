A few days ago our [Director of Technology and Development]
(http://www.nexus.globalquakemodel.org/author/pslh) asked me
a summary of the recent developments on the engine, for the
sake of reporting to the Governing Board. Since all the development
at [GEM](http://www.globalquakemodel.org/) is public, I thought that
I would post that same report on my blog too.

I went through the [code reviews]
(https://github.com/gem/oq-engine/pulls?direction=desc&page=1&sort=created&state=closed) from January 2014 up to now, to see
what is "new" in the engine. In that period the engine had more than
100 pull requests (!), so I am listing here only the major changes and
improvements.

1. A substantial part of the engine was removed. Lots of line
   of code, several database tables, and some dependencies (notably
   redis) were removed. We have now a code base which is much smaller
   and more maintainable.

2  Several delicate configuration parameters
   (hazard_block_size, risk_block_size, point_source_block_size,
   concurrent_tasks) were removed, thus reducing the burden on the
   final user. Now the engine is smart enough to deduce automagically
   the right parameters to use.

3. The distribution mechanism of the engine was unified and made more
   flexible. Moreover, we improved our usage of the underlying
   libraries (celery/rabbitmq) so that now it is possible to run
   hundreds of jobs simultaneously (notice jobs, not tasks)

4. The source model logic tree was decoupled from the gsim logic tree.
   This was a major undertaking, which allowed solving long standing
   inefficiencies. In particular we got huge speedups in computations
   with large logic trees, notably 140 times in an use case provided
   by one of our sponsors performing a computation with the SHARE model.

5. Huge improvements were obtained in the event based calculator. We do not
   store anymore multiple copies of the same rupture and we are ready to
   distribute the GMF computation by ruptures, with substantial performance
   benefits.

6. Now the sources are prefiltered according to the maximum distance before
   sending them to the workers, in all calculators. That helps in having
   more homogeneous tasks and makes a big performance improvement
   for site-specific analysis.

7. Area sources and fault sources are now automatically split by the
   engine. This also helps in producing homogeneous tasks and avoid a
   work that before was done manually by the hazard modelers.

8. We added support for non-parametric sources in the engine. Once
   non-parametric sources will be supported in nrmllib, we will be
   able to use them.

9. The engine server has been integrated inside the engine and its
   error reporting has been improved a lot. Also, the communication
   with the platform has been improved. Now the platform can just
   send a zip file to the engine server and have a computation performed.

10. The disaggregation calculator has been rewritten. Now it is is able
    parallelize properly, whereas before it was using a single core per site.
    In a real life computation (by Luis) the speedup was from 13 hours to
    30 minutes.

11. Substantial steps have been taken with the goal of decoupling the
    computations from the database. Now in all hazard calculators
    (except one case) there is no direct communications between the
    workers and the database, everything is mediated via rabbitmq.
    That means that the database is less of a bottleneck that it
    was before, at least for small logic trees.

12. A large portion of the engine code-base has been moved into a separate
    repository named oq-commonlib. In particular the logic tree management
    has been moved there and it is now pluggable, i.e. a scientist can
    override the default logic tree library with its own, by following
    a simple API.

13. A huge amount of work went into the risk calculators. Now finally
    they provide results which are fully deterministic; moreover the
    interaction with the database has been substantially improved in
    terms of both speed and memory consumption (of the order of 5 times).

14. Various infrastructural improvements were implemented. For instance now
    the engine includes a monitor checking for the availability of the nodes
    and providing sensible error messages in case of crashes.

15. Hundreds of bugs were fixed.

16. Huge improvements (one or two orders of magnitude in both speed
    and disk space occupation) on the database side for computations with
    large logic trees are expected in a week or two.

