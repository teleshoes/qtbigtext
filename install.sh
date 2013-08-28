#!/usr/bin/perl
use strict;
use warnings;

my $dest = "/opt/qtbigtext";

system "rm", "-rf", $dest;
system "mkdir", "-p", $dest;
system "cp src/* $dest";
