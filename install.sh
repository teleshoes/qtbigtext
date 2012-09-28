#!/usr/bin/perl
use strict;
use warnings;

my $dest = "/opt/qtbigtext";

system "mkdir", $dest;
system "cp src/* $dest";
