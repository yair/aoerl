#!/usr/bin/perl -w
use strict;
use JSON;

my $basedir = '/home/yair/w/aoerl/data/';
my @markets = `cd $basedir; ls -1 |xargs -n 1 ls |sort |uniq`;

my @m;
foreach (@markets) {
    chomp;
    /^BTC_/ and push @m, $_;
}

push @m, 'USDT_BTC';

print encode_json(\@m);
