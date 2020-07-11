#!/usr/bin/perl
use strict;
use warnings;

sub run(@);

my $binDest = "/usr/bin";
my $libDest = "/opt/qtbigtext";

sub main(@){
  run "sudo", "apt-get", "install", qw(
    python3-pyqt5 python3-dbus
  );

  run "sudo", "rm", "-rf", $libDest;
  run "sudo", "mkdir", "-p", $libDest;
  run "sudo", "cp", "src/bigtext", $binDest;
  run "sudo", "cp", "src/qtbigtext.py", $libDest;
}

sub run(@){
  print "@_\n";
  system @_;
}

&main(@ARGV);
