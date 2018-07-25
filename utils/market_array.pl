#!/usr/bin/perl -w

my $out = '';
while (<>) {
    chomp;
    if (/^(.*)$/) {
        $out .= "'$1', ";
    }
}

print $out
