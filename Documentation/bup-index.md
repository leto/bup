% bup-index(1) Bup %BUP_VERSION%
% Avery Pennarun <apenwarr@gmail.com>
% %BUP_DATE%

# NAME

bup-index - print and/or update the bup filesystem index

# SYNOPSIS

bup index <-p|-m|-u> [-s] [-H] [-l] [-x] [--fake-valid]
[--check] [-f *indexfile*] [--exclude *path*]
[--exclude-from *filename*] [-v] <filenames...>

# DESCRIPTION

`bup index` prints and/or updates the bup filesystem index,
which is a cache of the filenames, attributes, and sha-1
hashes of each file and directory in the filesystem.  The
bup index is similar in function to the `git`(1) index, and
can be found in `~/.bup/bupindex`.

Creating a backup in bup consists of two steps: updating
the index with `bup index`, then actually backing up the
files (or a subset of the files) with `bup save`.  The
separation exists for these reasons:

1. There is more than one way to generate a list of files
that need to be backed up.  For example, you might want to
use `inotify`(7) or `dnotify`(7).

2. Even if you back up files to multiple destinations (for
added redundancy), the file names, attributes, and hashes
will be the same each time.  Thus, you can save the trouble
of repeatedly re-generating the list of files for each
backup set.

3. You may want to use the data tracked by bup index for
other purposes (such as speeding up other programs that
need the same information).


# OPTIONS

-u, --update
:   (recursively) update the index for the given filenames and
    their descendants.  One or more filenames must be
    given.

-p, --print
:   print the contents of the index.  If filenames are
    given, shows the given entries and their descendants. 
    If no filenames are given, shows the entries starting
    at the current working directory (.).
    
-m, --modified
:   prints only files which are marked as modified (ie.
    changed since the most recent backup) in the index. 
    Implies `-p`.

-s, --status
:   prepend a status code (A, M, D, or space) before each
    filename.  Implies `-p`.  The codes mean, respectively,
    that a file is marked in the index as added, modified,
    deleted, or unchanged since the last backup.
    
-H, --hash
:   for each file printed, prepend the most recently
    recorded hash code.  The hash code is normally
    generated by `bup save`.  For objects which have not yet
    been backed up, the hash code will be
    0000000000000000000000000000000000000000.  Note that
    the hash code is printed even if the file is known to
    be modified or deleted in the index (ie. the file on
    the filesystem no longer matches the recorded hash). 
    If this is a problem for you, use `--status`.
    
-l, --long
:   print more information about each file, in a similar
    format to the `-l` option to `ls`(1).

-x, --xdev, --one-file-system
:   don't cross filesystem boundaries when recursing
    through the filesystem.  Only applicable if you're
    using `-u`.
    
--fake-valid
:   mark specified filenames as up-to-date even if they
    aren't.  This can be useful for testing, or to avoid
    unnecessarily backing up files that you know are
    boring.
    
--check
:   carefully check index file integrity before and after
    updating.  Mostly useful for automated tests.

-f, --indexfile=*indexfile*
:   use a different index filename instead of
    `~/.bup/bupindex`.

--exclude=*path*
:   a path to exclude from the backup (can be used more
    than once)

--exclude-from=*filename*
:   a file that contains exclude paths (can be used more
    than once)

-v, --verbose
:   increase log output during update (can be used more
    than once).  With one `-v`, print each directory as it
    is updated; with two `-v`, print each file too.


# EXAMPLE

    bup index -vux /etc /var /usr
    

# SEE ALSO

`bup-save`(1), `bup-drecurse`(1), `bup-on`(1)

# BUP

Part of the `bup`(1) suite.
