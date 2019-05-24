#!/usr/bin/perl -w
#use strict;
use v5.10;

# find out date boundaries.
my $end = 0, $start = 2147483647; # year 2038 bug
foreach (<*\/*>) {
    if (/^[A-Z_]+\/(\d{10})\d{3}\.pickle$/) {
        $1 < $start and $start = $1;
        $1 > $end   and $end   = $1;
    }
}
$start = int($start / 86400    ) * 86400;
$end   = int($end   / 86400 + 1) * 86400;
say 'Starting at '. gmtime($start). ' and ending at '. gmtime($end);

my $dstmpl = '%d-%02d-%02d';
mkdir 'splut' unless -e 'splut';
for (my $day = $start; $day < $end; $day += 86400) {
    my ($s,$m,$h,$mday,$mon,$year,,,) = gmtime($day);
    #    say "$mday/". ($mon + 1). "/". (1900 + $mday). " $h:$m:$s";
    #    say sprintf($dstmpl, $year + 1900, $mon + 1, $mday). " $h:$m:$s";
    #    mkdir "splut/". (1900 + $year). "-". ($mon + 1). "-$mday" unless -e "splut/". (1900 + $year). "-". ($mon + 1). "-$mday";
    mkdir "splut/". sprintf($dstmpl, $year + 1900, $mon + 1, $mday) unless -e "splut/". sprintf($dstmpl, $year + 1900, $mon + 1, $mday);
}

foreach (<*\/*>) {
    /^([A-Z_]+)\/(\d{10})(\d{3}\.pickle)$/ or next;
    my $pday = 86400 * int($2 / 86400);
    my ($s, $m, $h, $mday, $mon, $year,,,) = gmtime($pday);
    my $pts = sprintf($dstmpl, $year + 1900, $mon + 1, $mday);
    -e "splut/$pts" or die "Can't find folder splut/$pts for ". gmtime($pday). "\n";
    -e "splut/$pts/$1" or mkdir "splut/$pts/$1";
    say "Moving $_ to splut/$pts/$1/$2$3";
    rename $_, "splut/$pts/$1/$2$3";
}

foreach (<splut/*>) {
    `tar cJf bnfrag_$_.txz $_`;
}
=cut

# Splits older from newer fragment files

use constant OLD    => 'old';
use constant DRY    => 0;
# Binance - 3 months is a snug fit, so sometimes we have only one and a half. Cut it into smaller pieces.
# Poloniex - 
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
}*/
