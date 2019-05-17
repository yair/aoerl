#!/usr/bin/perl -w
#use strict;
use v5.10;

# Splits older from newer fragment files

use constant OLD    => 'old';
use constant DRY    => 0;
# Binance - 3 months is a snug fit
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
use constant CUTOFF => 1556668800000; # 20190501

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
