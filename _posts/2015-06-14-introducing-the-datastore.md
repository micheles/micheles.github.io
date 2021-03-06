---
layout: post
title: Introducing the DataStore (i.e. HDF5 rocks)
---

As I said several times in this blog, the single biggest
mistake in the architecture of the engine was the pervasive use of a
relational database in numerical code. It should be obvious that
performance-critical code cannot affort to wait for the
database to read and write gigabytes of data. Unfortunately this was
not clear to the original designers of the engine, who fortunately I have
never met. Basically, I have spent of all my time at GEM fighting
against this original sin. But now, after nearly three years, I am
starting to win.

The key to the victory has a cryptic-looking name,
[HDF5](https://www.hdfgroup.org/HDF5/), which stands
both for a file format and a library to read and write numeric data in
that format. HDF5 is well known
among data analysts and numeric scientists; actually the GEM scientific
team has been wanting to use this format from day one, even if, for
mysterious reasons, the original IT team never wanted to hear them.
Personally I have never been doing any numeric-intensive code before
coming to GEM, so HDF5 was unknown to me, but I was inclined to
believe our scientists. Therefore HDF5 was my top priority as
technology to replace PostgreSQL in the engine from the beginning.  However,
it was clear that replacing the database was a major
effort, so instead on starting right away in that direction I spent
two years of my life trying to come to terms with the database. After
all, I had 7 years of experience with relational databases, and I was
much more of a database expert than the developers that preceeed me at
GEM, so I was able to do a lot of improvements. Nevertheless, it was
a uphill battle, with some victories on my part, but
a final defeat last summer, when I tried to optimize the event based
risk calculator. After over two months of hard effort it became clear
to me that there was absolutely no hope of winning the war with
optimizations on the database side. I was able to gain more than an
order of magnitude of performances by changing the database structure:
but a gain of a factor 20-30 was nothing, I needed to improve the
reading speed of the data by at least *two or three orders of
magnitude* to be competive with the calculation time.

The end of summer 2014 marked the end of my direct confrontation with
the database: by that time I managed to convince the GEM people that
we needed to go in a different direction. The codename for the new
course was "oq-lite", i.e. a lite version of the engine able to run on
consumer machines and *without a database*. Starting from September
2014 most of my time has been spent working on oq-lite, whereas the
engine entered maintenance mode. This became possible because no new
features were planned for the engine and we entered in a consolidation
phase of the previous work.

For the first 6 months oq-lite did not address the database problem
at all: since it was originally meant for small computations, it could afford
to keep everything in memory and to export everything in CSV. However,
such an approach was not sustainable for large computations, especially
for risk ones, when one wants to store the hazard results to avoid
recomputing them every time a new risk calculation is started. In the
engine the hazard data is stored in the database: in oq-lite I needed
a replacement for it. Since the hazard data were basically numpy arrays
I needed an efficient storage for that, i.e. an HDF5 file. A
couple of months ago I started to study the
[h5py](http://docs.h5py.org/en/latest/) library, which allows to
manage HDF5 files from Python. I liked this library from the first
day, since it is really simple to use, nice, Pythonic, and makes a
lot of sense for people familiar with [numpy](http://www.numpy.org/).
After a while I liked h5py even more, and the more I use it, the more I like
it: *HDF5 rocks!*

It is a nice library, that tries to do as little than possible and
does it well. The only shortcoming that I see are some error messages
that could be improved, but it is not difficult to work around that.
In the Python world there is also another library working with
HDF5 files, i.e. [PyTables](http://www.pytables.org/). PyTables does
much more than h5py, and it is essential an ORM with an HDF5 backend
instead than a database. I liked h5py much more than PyTables, since it
is perfect for what I wanted to do with oq-lite: a storage facility
that does not require a database and that *does not even resemble
a database*. For the purpose of the GEM calculators the natural
data structure to use is a dictionary key -> value, where the
key is a string and the value is a numpy array.

I encoded this data structure into a dict-like class called DataStore
and I was ready to go. The DataStore class is a small (< 200 lines of
code), has all the features needed for the persistency needs of the
GEM calculators and nothing more. Its performances are incredibly
better than what Postgres can provide. This is to be expected, since
the HDF5 file format is specialized to store arrays and has none of
the transactional and concurrency features of a relational
database. Incidentally, let me say that I strong believer in relation
databases, I like Postgres a lot and I have a huge experience with it:
it is the right tool for many things, just not for
multidimensional composite arrays of floats spanning gigabytes. There
it cannot compete with HDF5, nor in terms of performances nor in terms
of simplicity of use.

In a future blog post I will explain how you can use the datastore. Stay tuned!


