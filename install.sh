#!/usr/bin/perl
use strict;
use warnings;

my $binDest = "/usr/bin";
my $libDest = "/opt/qtbigtext";

system "rm", "-rf", $libDest;
system "mkdir", "-p", $libDest;
system "cp", "src/bigtext", $binDest;
system "cp", "src/qtbigtext.py", $libDest;
