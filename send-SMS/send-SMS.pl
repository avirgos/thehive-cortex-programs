#!/usr/bin/perl

use strict;
use LWP::Simple;
use URI::Escape;

my $number = $ARGV[0];
my $msg = uri_escape($ARGV[1]);

my @servers = ("sms-server1", "sms-server2");
my $port = "8000";
my $path = "/SMS?pwd=******&number=$number&notification=1&text=";
my $error = 0;

sub get_current_time {
    my $now = `date "+%d/%m/%Y %H:%M:%S"`;
    chomp $now;
    return $now;
}

sub test_connexion {
    my ($server, $port) = @_;
    my $url_base = "http://$server:$port";
    my $return = get($url_base);
    return $return ? 1 : 0;
}

sub send_sms {
    my ($server, $port, $number, $msg) = @_;
    my $url = "http://$server:$port/SMS?pwd=******&number=$number&notification=1&text=$msg";

    my $return = get($url);

    if (defined $return && $return =~ /<error_code>0<\/error_code>/) {
        return (1, $return);
    } else {
        return (0, $return);
    }
}

foreach my $server (@servers) {
    my $now = get_current_time();
    print "$now;$server;Message;Start of connection test.\n";

    if (!test_connexion($server, $port)) {
        print "$now;$server;Error;Access to $server not possible. Sending of SMS cancelled.\n";
        print "$now;$server;Error;End of connection test.\n";
        $error = 1;
        next;
    }

    print "$now;$server;Message;Error-free connection test. SMS sent.\n";

    my ($sms_sent, $return) = send_sms($server, $port, $number, $msg);

    if ($sms_sent) {
        print "$now;$server;Message;SMS sent without error : \n$return\n";
        $error = 0;
        last;
    } else {
        print "$now;$server;Error;Failed to send sms : \n$return\n";
        $error = 1;
    }
}

exit $error;