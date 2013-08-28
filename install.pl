#!/usr/bin/perl
use strict;
use warnings;

my $binDest = "/usr/bin";
my $libDest = "/opt/qtbigtext";

system "sudo", "apt-get", "install", qw(
  python3-pyside python3-dbus
);
system "sudo", "rm", "-rf", $libDest;
system "sudo", "mkdir", "-p", $libDest;
system "sudo", "cp", "src/bigtext", $binDest;
system "sudo", "cp", "src/qtbigtext.py", $libDest;
