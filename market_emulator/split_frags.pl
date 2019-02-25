#!/usr/bin/perl -w
use strict;
use v5.10;

# Splits older from newer fragment files

use constant OLD    => 'old';
use constant DRY    => 0;
use constant CUTOFF => 1543622400000; # 20181201

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
