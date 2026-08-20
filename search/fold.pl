#!/usr/local/bin/perl
;#
;# fold.pl: line folding library for Perl as well as a fold(1) clone.
;#
;# You can include this file from other Perl program or execute
;# directly as a command.
;#
;# Copyright (c) 1995,1998 Kazumasa Utashiro <utashiro@iij.ad.jp>
;# Internet Initiative Japan Inc.
;# 3-13 Kanda Nishiki-cho, Chiyoda-ku, Tokyo 101-0054, Japan
;#
;# Copyright (c) 1993 Kazumasa Utashiro
;# Software Research Associates, Inc.
;#
;# Original version: 25 Mar 1993
;# #Id: fold.pl,v 1.5 1998/12/26 00:32:37 utashiro Exp #
;#

if (__FILE__ eq $0) {
    $myname = ('whoami?', split('/', $0));
    Usage:					$usage = <<"    ;";
	$myname [-width] [-w] [-p]
	-width: specify folding width (default 80)
	-w:	fold on word boundaries
	-p:	put padding spaces at the end of line
	-t:	truncate by width
	-f:	replace final newline by space and fill text
	-s:	delete leading space
    ;
    $width = 80;
    while ($_ = $ARGV[$[], s/^-(.+)$/$1/ && shift) {
	next unless length;
	if (s/^(\d+)//) { $width = $1;   redo; }
	if (s/^w//)     { $onword = 1;   redo; }
	if (s/^p//)     { $padding = 1;  redo; }
	if (s/^t//)     { $truncate = 1; redo; }
	if (s/^f//)     { $/ = '';       redo; }
	if (s/^s//)     { $delete_leading_space = 1; redo; }
	if (s/^e//)     { ($expand = shift) && redo; }
	print STDERR "Usage:", $usage, "$rcsid\n"; exit(!/^h/);
    }
    while (<>) {
	while (length) {
	    s/\n([^\n])/ $1/g;
	    ($l, $_) = &fold($_, $width, $padding, $onword, $expand);
	    $l =~ s/^ // if $delete_leading_space;
	    print $l;
	    print "\n" if length;
	    last if $truncate;
	}
    }
    exit(0);
}

######################################################################

package fold;
;#
;# SYNOPSIS
;#
;#	($folded, $rest) = &fold(LINE, WIDTH, PADDING, ONWORD, EXPAND, COLUMN);
;#
;# DESCRIPTION
;#
;#	Pass the line to be folded as a first argument and folding width as
;#	a second argument.  If optional third argument is true, space
;#	character will be padded at the end of the line if necessary.  If
;#	the fourth argument is true, the line is folded on the word
;#	boundaries.  The fifth argument is a string which specifies what
;#	character is expanded by spaces and backspaces ('r' for carriage
;#	return, 't' for tab and 'a' for all).  The sixth argument specifies
;#	start column of the string to caliculate tab stop.
;#
;#	Return value is a list of a folded line and the rest.
;#
;; $rcsid = q#Id: fold.pl,v 1.5 1998/12/26 00:32:37 utashiro Exp #;
;#	
sub main'fold {
    local($_, $width, $padding, $onword, $expand, $start) = @_;
    local($l, $room) = ('', $width);
    local($n, $c, $r, $mb);

    while (length) {
	if (s/^\cH//) {
	    $c = "\cH";
	    if ($room < $width) {
		$room++;
	    } elsif ($start > 0) {
		$start--;
	    }
	    next;
	}
	if (s/^\r//) {
	    if ($expand =~ /[ar]/) {
		$c = "\cH" x ($width - $room + $start);
	    } else {
		$c = "\r";
	    }
	    $room = $width + $start;
	    $start = 0;
	    next;
	}
	last if $room <= 0 || (/^[\200-\377]/ && $room < 2);
	if (s/^\t//) {
	    $space = 8 - ($start + $width - $room) % 8;
	    if ($expand =~ /[at]/) {
		$_ = (' ' x $space) . $_;
		redo;
	    } else {
		$room -= $space;
		$c = "\t";
		$l .= $c, last if $room <= 0;
		next;
	    }
	}
	if (($mb = s/^(([\200-\377].)+)//) || s/([^\t\b\r\200-\377]+)//) {
	    $n = $room;
	    $n -= $room % 2 if $mb;
	    ($c, $r) = unpack("a$n a*", $1);
	    $room -= length($c);
	    $_ = $r . $_;
	} else {
	    die "&fold: panic";
	}
    } continue {
	$l .= $c;
    }
    if ($onword && /^\w/ && !$mb && $l =~ s/([^\w\b])([\w\b]+)$/\1/) {
	$cut = $2;
	if ($l =~ /[\200-\377]$/) { # This check is not necessary for EUC
	    local(@tmp) = $l =~ /[\200-\377]?./g;
	    (pop(@tmp) =~ /^[\200-\377]$/) && ($cut =~ s/^(.)//) && ($l .= $1);
	}
	$_ = $cut . $_;
	$room += &pwidth($cut) if $padding;
    }
    $l .= ' ' x $room if $padding;
    ($l, $_);
}

sub pwidth {
    local($_) = @_;
    return(length) unless /[\cH\f\r]/;
    s/^.*[\f\r]//;
    1 while s/[^\cH]\cH//;
    s/^\cH+//;
    length;
}

1;
