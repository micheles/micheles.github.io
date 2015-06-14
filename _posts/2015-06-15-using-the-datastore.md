---
layout: post
title: Using the DataStore
---

In a [previous post](/2015/06/14/introducing-the-datastore) I told the story
behind the DataStore class. Today I will show how to use it.
A DataStore instance is a dictionary-like object built around
an underlying HDF5 file. An HDF5 file is a dictionary-like object
with keys which are strings of the form `"/some/path/to/the/data"`.
The values are basic data types i.e. integers, floats,
strings, and arrays, which can be stored efficiently.
You can learn the concepts about HDF5
files [here](http://docs.h5py.org/en/latest/). The DataStore
is a thin wrapper over a `h5py.File` object.
You can use it as follows:

```python
  >>> import numpy
  >>> from openquake.commonlib.datastore import DataStore

  >>> ds = DataStore()  # instantiate a datastore
  >>> ds.hdf5  # the underlying h5py.File instance
  <HDF5 file "output.hdf5" (mode r+)>

  >>> key = '/some/data'
  >>> value = numpy.array([[1, 2], [3, 4]])
  >>> ds[key] = value  # store the array on the underlying HDF5 file
  >>> ds[key]  # retrieve the dataset from the HDF5 file
  <HDF5 dataset "data": shape (2, 2), type "<i8">
  >>> ds[key].value # retrieve the array from the dataset
  array([[1, 2], [3, 4]])

  >>> list(ds) # show the keys in the HDF5 file
  [u'/some']
  >>> list(ds['/some'])  # show the keys in the group '/some'
  [u'data']
```

All of the regular methods of a Python dictionary are available. The
DataStore is more than a wrapper of a HDF5 file, and actually it is
able to persist any pickleable Python object. In fact, the HDF5
file is used solely for numpy arrays, whereas general Python objects
are save in the datastore directory as pickled files. However arrays are the most
important objects that need storing in the oq-lite calculators, and the plan
for the future is to replace as much as possible Python objects with numpy
arrays, which are much much more efficiently stored and moved around.
You can see the full documentation of the datastore module at
[docs.openquake.org](http://docs.openquake.org/oq-risklib/master/openquake.commonlib.html#module-openquake.commonlib.datastore).

One important thing to remember is that *the datastore does not support
concurrent writing*. This is due both to a limitation in the underlying
h5py library and to an architectural constraint: when doing parallel
computations in the oq-lite we adhere to a strict
master/slave approach: only the master is allowed to read/write
on the datastore, whereas *the workers do not have access
to the datastore*. This paradigm makes everything simple and clean,
so that the concurrent writing limitation simply disappear, since
only the master can write and the master is a single threaded process.

The case of running concurrent calculations is managed in the simplest
possible way: each time a datastore is instantiate a new directory is
created and a HDF5 file called `output.hdf5` is created
inside that directory. The location of the directory
is determined by the environment variable $OQ_DATADIR. If the variable
is not set, the datastore uses the directory $HOME/oqdata as base
path for the datastore directories. When a DataStore is instantiated,
the base directory is searched (it is automatically created if not found)
and directories with names following the pattern `calc_<ID>` are retrieved.
If nothing is found, a directory called `calc_1` is created
and the datastore instance grows an attribute `calc_id` with value `1`;
otherwise, the highest `calc_id` is retrieved from the found calculation
directories and a new directory is created with calculation ID
`calc_id + 1`. In this way each calculation writes in its own directory;
in multiuser situations there is no conflict since each user by default
writes on its own home directory. Notice that at the moment the datastore
does not offer any protection against race conditions and in theory 
two different calculations could get the same `calc_id`. That may change
in the future. In practice, calculations are started manually, there
are seconds between one and the next, so race conditions never
happen.

I will close this post with a short routine that performs a classical
calculation and save the results in the datastore, so that you can
see how it works in practice:

```python
from openquake.baselib.general import groupby
from openquake.commonlib import readinput, datastore
from openquake.hazardlib.calc.hazard_curve import hazard_curves_per_trt

def compute_classical_psha(job_ini):
    # read the configuration file
    oq = readinput.get_oqparam(job_ini)
    # read the site collection
    sitecol = readinput.get_site_collection(oq)
    # read the source model
    csm = readinput.get_composite_source_model(oq, sitecol)
    # group the sources by tectonic region model ID
    sources_by_trt_id = groupby(csm.get_sources(),
                                lambda src: src.trt_model_id)
    # dictionary trt_model_id -> list of GSIMs
    gsims_assoc = csm.get_rlzs_assoc().get_gsims_by_trt_id()
    # instantiate an empty datastore
    dstore = datastore.DataStore()
    # sequentially compute the curves for earch tectonic region type
    for trt_id, sources in sources_by_trt_id.iteritems():
        trt = sources[0].tectonic_region_type
        print 'Considering trt_model_id=%s, TRT=%s' % (trt_id, trt)
        gsims = gsims_assoc[trt_id]
        # a list of curves, one for each GSIM
        all_curves = hazard_curves_per_trt(
            sources, sitecol, oq.imtls, gsims)
        # saving the curves in the datastore
        for gsim, curves in zip(gsims, all_curves):
            dskey = '/%s/%s' % (trt_id, gsim)
            print 'Saving %s' % dskey
            dstore[dskey] = curves
            # flush the curves on the HDF5 file
            dstore.flush()
    dstore.close()
    print 'See the results with hdfview %s/output.hdf5' % dstore.calc_dir
```

[hdfview](https://www.hdfgroup.org/products/java/hdfview/) is a Java
tool to visualize and edit HDF5 files (the advantage of using
standards: we did not have to write it).

Incidentally, let me point out that this ~20=line routine is
essentially doing 90% of the work than in the original oq-engine was
done in ~10000 lines of code (most of them spent in defining database
tables that here are simply not needed) ~100 times less efficiently.

The calculation here is sequential. Making it parallel requires just
two more lines, but it is left for another post, to keep the
suspense. Stay tuned!
