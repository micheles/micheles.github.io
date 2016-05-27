---
layout: post
title: A list of oq-lite commands
---

The command-line utility `oq-lite` is going to die. The plan for the
release 2.0 of the engine is to remove it. However, it will be a
phoenix death, since it will be resurrected with the name `oq-engine`:
it will be the old `oq-engine` command that will go, really.

This is the plan, however, things can change, especially if the users
protest that they want the old `oq-engine` command
unchanged. Since nothing is decided, and since engine 2.0 is
not out yet, in the meanwhile it is useful to document the main
(sub)commands of `oq-lite`.

The first and most important one is the `help` command, which at
the moment looks like this:

```bash
$ oq-lite help
usage: oq-lite [-v]
                   {upgrade_nrml,purge,reduce,tidy,show,export,show_attrs,run,info,plot,help}
                   ...

positional arguments:
  {upgrade_nrml,purge,reduce,tidy,show,export,show_attrs,run,info,plot,help}
                        available subcommands; use help <cmd>

optional arguments:
  -v, --version         show program's version number and exit
```

By running

```bash
$ oq-lite help <name-of-a-specific-subcommand>
```

it is possible to get help on specific subcommands.

`oq-lite` is still experimental, so there are still commands that do
not work properly (`tidy`) or are limited preview of things to come
(`plot`); other commands may be added and the name and options of
the command may change. The rule is that if a command is not
documented properly in the OpenQuake manual, this is done on
purpose and you should not rely on that command.

The most commonly used oq-lite commands
-------------------------------------------------

`oq-lite info`: this the most important command for somebody running
a computation. You should run it *before* running the computation
since it will give you a lot of useful information.

```bash
$ oq-lite help info
usage: oq-lite info [-h] [-c] [-g] [-v] [-r] [input_file]

positional arguments:
  input_file         job.ini file or zip archive [default: ]

optional arguments:
  -h, --help         show this help message and exit
  -c, --calculators  list available calculators
  -g, --gsims        list available GSIMs
  -v, --views        list available views
  -e, --exports      list available exports
  -r, --report       build a report in rst format
```

`oq-lite info --calculators` gives the full list of calculators implementedin the engine.

`oq-lite info --gsims` gives the full list of available Ground Shaking
Intensity Models (GSIMs), implemented in our hazard library (hazardlib).

`oq-lite info --views` gives the full list of datastore views implemented in
the engine. They are calculator-dependent and can be used in conjunction
with the `oq-lite show` command, as we will document later on.

`oq-lite info --exports` gives the full list of available exporters.
Most of them are calculator specific.

`oq-lite info job.ini` prints information about the logic tree of
the calculation specified by the `job.ini` file (it also works
on a zip archine, if it contains a `job.ini` file). This command
is very fast. The price to pay is that it does not filter the sources
of the source model depending on the sites, so it may produce a
logic tree larger than the one that would be effectively used.

`oq-lite info --report job.ini` prints a lot more information. It is slow, but
still much faster than doing the full computation. Since it filters
the sources, it produces accurate information about the logic
tree that would be used by the full computation. In the case of an event
based calculation it also samples all the ruptures that would be
sampled in the real computation.

`oq-lite run` actually runs a computation. It is the most
complex command there is, but also the most important.

```bash
$ oq-lite help run
usage: oq-lite run [-h] [-s SLOWEST] [--hc HC] [-p PARAM [PARAM ...]] [-c 8]
                   [-e] [-l info] [-d]
                   job_ini

Run a calculation.

positional arguments:
  job_ini               calculation configuration file (or files, comma-
                        separated)

optional arguments:
  -h, --help            show this help message and exit
  -s SLOWEST, --slowest SLOWEST
                        profile and show the slowest operations
  --hc HC               previous calculation ID
  -p PARAM [PARAM ...], --param PARAM [PARAM ...]
                        override parameter with the syntax NAME=VALUE ...
  -c 8, --concurrent-tasks 8
                        hint for the number of tasks to spawn
  -e , --exports        export formats as a comma-separated string
  -l info, --loglevel info
                        logging level
  -d, --pdb             enable post mortem debugging
```

`oq-lite show`: this extracts information from a computation which has
already run.

```bash
$ oq-lite help show
usage: oq-lite show [-h] what [calc_id]

Show the content of a datastore (by default the last one).

positional arguments:
  what        key or view of the datastore
  calc_id     calculation ID [default: -1]

optional arguments:
  -h, --help  show this help message and exit
```
  
The engine provides a number of useful views over the datastore,
all accessible via the `oq-lite show` command.

`oq-lite export` exports the outputs of a computation from the datastore
to XML, CSV or TXT files. The calculation is specified with a integer
`calc_id`; if not specified, exports from the last calculation.
Negative `calc_id` are allowed; `-1` mean the last calculation,
`-2` means the calculation before the last, and so on.

```bash
$ oq-lite export -h
usage: oq-lite export [-h] [-e csv] datastore_key [export_dir] [calc_id]

positional arguments:
  datastore_key         datastore key
  export_dir            export directory [default: .]
  calc_id               number of the calculation [default: -1]

optional arguments:
  -h, --help            show this help message and exit
  -e csv, --exports csv
                        export formats (comma separated)
```

Less used commands
---------------------

`oq-lite show_attrs` show the attributes of dataset in the datastore.
This is useful when you run your computation in a server which has
no graphical interface, and you want to look at the metadata of
some specific dataset. Normally, you would just open the datastore
with `hdfview` and look at the attributes there.

```bash
$ oq-lite show_attrs -h
usage: oq-lite show_attrs [-h] key [calc_id]

Show the attributes of a HDF5 dataset in the datastore.

positional arguments:
  key         key of the datastore
  calc_id     calculation ID [default: -1]

optional arguments:
  -h, --help  show this help message and exit
```

`oq-lite purge` allows to remove old datastores.

```bash
$ oq-lite purge -h
usage: oq-lite purge [-h] calc_id

Remove the given calculation. If calc_id is 0, remove all calculations.

positional arguments:
  calc_id     calculation ID

optional arguments:
  -h, --help  show this help message and exit
```

`oq-lite upgrade_nrml` upgrades all the XML file in a directory that
needs to be upgraded. This is useful only for old time users that
still have models in format NRML 0.4, while the current format is
NRML 0.5

```bash
$ oq-lite upgrade_nrml -h
usage: oq-lite upgrade_nrml [-h] [-d] directory

Upgrade all the NRML files contained in the given directory to the latest NRML
version. Works by walking all subdirectories. WARNING: there is no downgrade!

positional arguments:
  directory      directory to consider

optional arguments:
  -h, --help     show this help message and exit
  -d, --dry-run  test the upgrade without replacing the files
```
