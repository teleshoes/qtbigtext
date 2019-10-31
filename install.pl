#!/usr/bin/perl
use strict;
use warnings;

sub run(@);

my $binDest = "/usr/bin";
my $libDest = "/opt/qtbigtext";

sub main(@){
  run "sudo", "apt-get", "install", qw(
    python3-pyside python3-dbus
    python-dbus
  );

  run "sudo", "python", "-m", "easy_install", "pyside2";

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
