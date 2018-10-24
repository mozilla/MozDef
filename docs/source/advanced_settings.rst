Advanced Settings
=================

Conf files
----------
MozDef python scripts in almost all cases expect to be given a -c path/to/file.conf command line option to specify configuration/run time options.

These files all follow the same format:

::

    [options]
    setting1=value1
    setting2=value2


All programs do their best to set reasonable, sane defaults and most will run fine without a conf file. By default programname.py will look for programname.conf as it's configuration file so if you follow that convention you don't even need to specify the -c path/to/file.conf option.

Special Config Items
_____________________

Here are some tips for some key settings:

::

    [options]
    esservers=http://server1:9200,http://server2:9200,http://server3:9200

is how you can specify servers in your elastic search cluster.

::

    [options]
    backup_indices = intelligence,.kibana,alerts,events,complianceitems,.jsp,.marvel-kibana,vulnerabilities
    backup_dobackup = 1,1,1,1,1,1,1,1
    backup_rotation = none,none,monthly,daily,none,none,none,none
    backup_pruning = 0,0,0,20,0,0,0,0

is how you would configure the backupSnapshot.py and pruneIndexes.py programs to backup selected elastic search indexes, rotate selected indexes and prune certain indexes at selected intervals. In the case above we are backing up all indexes mentioned, rotating alerts monthly, rotating events daily and pruning events indices after 20 days.

::

    [options]
    autocategorize = True
    categorymapping = [{"bruteforce":"bruteforcer"},{"nothing":"nothing"}]

is how you would configure collectAttackers.py to do autocategoization of attackers that it discovers and specify a list of mappings matching alert categories to attacker category.
