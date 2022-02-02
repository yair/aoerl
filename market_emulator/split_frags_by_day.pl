#!/usr/bin/perl -w
use strict;
use v5.10;

#my $exch = 'binance';
my $exch = 'poloniex';

# Splits fragment file repo into smaller, daily repos.

use constant OLD    => 'old';
use constant DRY    => 0;
use constant MSID   => 86400000; # millisecond in day

# Find out first and last days
my $fday_start = 2147483647000;
my $lday_end   = 0;

foreach my $mart (<*BTC*>) {
    foreach my $fn (<$mart/*>) {

        if ($fn =~ /^$mart\/(\d+)\.pickle$/) {
            my $day = $1; # int? float?
            $fday_start = $day if ($day < $fday_start);
            $lday_end   = $day if ($day > $lday_end);
        } else {
            say("Unrecognized file pattern $fn");
        }
    }
}
$fday_start = MSID * int($fday_start / MSID);
#$lday_end   = 1559347200000; # MSID * (1 + int($lday_end / MSID));              June first. *** CHANGE ME ***
#$lday_end   =  1560643200000; # MSID * (1 + int($lday_end / MSID));              June 16th. *** CHANGE ME ***
$lday_end   = MSID * (1 + int($lday_end / MSID));
#say("fday_start=$fday_start lday_end=$lday_end");
say('Splitting into ' . ($lday_end - $fday_start) / MSID . ' days from ' . gmtime($fday_start/1000) . ' to ' . gmtime($lday_end/1000));

for (my $day = $fday_start; $day < $lday_end; $day += MSID) {

    if (DRY) {
        say('Would have moved all files from ' . gmtime($day / 1000) . ' to ' . gmtime(($day + MSID) / 1000));
    } else {
        mkdir OLD unless -e OLD;
        &move_files_in_range($day, $day + MSID);
        my ($s, $m, $h, $mday, $mon, $year,,,) = gmtime($day/1000);
        my $tarball_fn = sprintf("../${exch}_fragments_%04d%02d%02d.txz", $year + 1900, $mon + 1, $mday);
        say("Creating tarball $tarball_fn");
        `cd old; tar cJf $tarball_fn *` and die "Could no create daily tarball for ' . gmtime($day/1000) . ': $?, $!\n";
        `rm -Rf old` and die "Could not remove old: $?, $!\n";
#        exit(0);
    }
}

# REMOVE TESTING DUPE AT ADABTC/1554773237157.pickle

sub move_files_in_range {

    my ($from, $to) = @_;

    foreach my $mart (<*BTC*>) {

        mkdir OLD . "/$mart" unless -e OLD . "/$mart";

        foreach my $fn (<$mart/*>) {

            if ($fn =~ /^$mart\/(\d+)\.pickle$/) {

#                if ($1 < CUTOFF) {
                if ($1 >= $from and $1 < $to) {

                    if (DRY) {

                        say "Would have moved $1.pickle to " . OLD . "/$mart/";
                    } else {

                        rename "$mart/$1.pickle", OLD . "/$mart/$1.pickle" or die "Could not move $mart/$1.pickle to " . OLD . "/$mart/ : $0, $!, $?\n";
                        say "Moved $1.pickle to " . OLD . "/$mart/";
                    }
                }
            } else {
                say "Unrecognized file name format $fn (mart=$mart)";
            }
        }
    }
}

exit(1);


# For each day, run the basic functionality, then compress the contents of 'old' to a root dir file and delete 'old' contents.


# Binance - 3 months is a snug fit, so sometimes we have only one and a half. Cut it into smaller pieces.
# Poloniex - 
#use constant CUTOFF => 1530403200000; # 20180701
#use constant CUTOFF => 1533081600000; # 20180801
#use constant CUTOFF => 1535760000000; # 20180901
#use constant CUTOFF => 1538352000000; # 20181001
#use constant CUTOFF => 1541030400000; # 20181101
#use constant CUTOFF => 1543622400000; # 20181201
#use constant CUTOFF => 1546300800000; # 20190101
#use constant CUTOFF => 1548979200000; # 20190201
#use constant CUTOFF => 1551398400000; # 20190301
#use constant CUTOFF => 1554076800000; # 20190401
#use constant CUTOFF => 1556668800000; # 20190501
=cut
use constant CUTOFF => 1554854400000; # 20190410

mkdir OLD unless -e OLD;

#foreach my $mart (glob (<*BTC*>)) {
foreach my $mart (<*BTC*>) {

    mkdir OLD . "/$mart" unless -e OLD . "/$mart";

    foreach my $fn (<$mart/*>) {

        if ($fn =~ /^$mart\/(\d+)\.pickle$/) {

            if ($1 < CUTOFF) {

                if (DRY) {

                    say "Would have moved $1.pickle to " . OLD . "/$mart/";
                } else {

                    rename "$mart/$1.pickle", OLD . "/$mart/$1.pickle" or die "Could not move $mart/$1.pickle to " . OLD . "/$mart/ : $0\n";
                    say "Moved $1.pickle to " . OLD . "/$mart/";
                }
            }
        } else {
            say "Unrecognized file name format $fn (mart=$mart)";
        }
    }
}
