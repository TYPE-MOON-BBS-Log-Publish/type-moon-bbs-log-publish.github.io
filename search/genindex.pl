#!/usr/local/bin/perl
#=============================================================================#
#                                                                             #
#                        msearch - mat's search program                       #
#                                version 1.50                                 #
#                                                                             #
#                  超簡易インデックス版検索エンジンプログラム                 #
#        Copyright (C) 2000-2003, Katsushi Matsuda. All Right Reserved.       #
#                                                                             #
#=============================================================================#

#=============================================================================#
#                         インデックス作成プログラム                          #
#=============================================================================#

require './jcode.pl';		# 漢字コード変換パッケージ
require './indexing.pl';        # インデックス作成モジュール

####################
### 変更可能変数 ###
####################

### デバッグ時にのみ設定して下さい．
### 0 - デバッグ情報出力なし
### 1 - 出力する
$debug = 0;


##################
### メイン処理 ###
##################

### 表示
print "genindex.pl -- index generator for msearch\n";
print "Copyright (c) 2000-2003 Katsushi Matsuda. All Right Reserved.\n";
print "Display kanji code is ";

### 出力漢字コードの決定
if($ARGV[0] =~ /-s/i || $ARGV[0] =~ /-sjis/i) {
    $kanji = "SJIS";
    print "SJIS";
} elsif($ARGV[0] =~ /-j/i || $ARGV[0] =~ /-jis/i) {
    $kanji = "JIS";
    print "JIS";
} else {
    $kanji = "EUC";
    print "EUC";
}
print "\n\n";

### 引数の取得とパージング
printout("インデックスの名前は？\n> ");
$qarg->{'index'} = <STDIN>;
chomp($qarg->{'index'});
$qarg->{'index'} =~ s/ //g;

printout("インデックス対象ディレクトリは？(必須)\n> ");
$qarg->{'includedir'} = <STDIN>;
chomp($qarg->{'includedir'});
$qarg->{'includedir'} =~ s/ //g;

printout("インデックス対象ディレクトリのURLは？(必須)\n> ");
$qarg->{'includeurl'} = <STDIN>;
chomp($qarg->{'includeurl'});
$qarg->{'includeurl'} =~ s/ //g;

printout("インデックス対象ファイルの拡張子は？(必須)\n> ");
$qarg->{'suffix'} = <STDIN>;
chomp($qarg->{'suffix'});
$qarg->{'suffix'} =~ s/ //g;

printout("非インデックス対象ディレクトリは？\n> ");
$qarg->{'excludedir'} = <STDIN>;
chomp($qarg->{'excludedir'});
$qarg->{'excludedir'} =~ s/ //g;

printout("非インデックス対象ファイルは？\n> ");
$qarg->{'excludefile'} = <STDIN>;
chomp($qarg->{'excludefile'});
$qarg->{'excludedir'} =~ s/ //g;

printout("非インデックス対象キーワードは？\n> ");
my $tmpstr = <STDIN>;
if($kanji eq "SJIS") {
    &jcode::convert(\$tmpstr,"euc");
}
$qarg->{'excludekey'} = $tmpstr;
chomp($qarg->{'excludekey'});
$qarg->{'excludedir'} =~ s/ //g;

printout("ランキング方法は？\n");
printout("[1] 最終更新日時-降順\n");
printout("[2] 最終更新日時-昇順\n");
printout("[3] タイトル-降順\n");
printout("[4] タイトル-昇順\n");
printout("[5] URL-降順\n");
printout("[6] URL-昇順\n");
printout("[0] なし\n");
printout("どれにしますか？[0〜6] > ");
$tmp = <STDIN>;
chomp($tmp);
if($tmp == 1) {
    $qarg->{'sort'} = "MODIFY-DESC";
} elsif($tmp == 2) {
    $qarg->{'sort'} = "MODIFY-ASC";
} elsif($tmp == 3) {
    $qarg->{'sort'} = "TITLE-DESC";
} elsif($tmp == 4) {
    $qarg->{'sort'} = "TITLE-ASC";
} elsif($tmp == 5) {
    $qarg->{'sort'} = "URL-DESC";
} elsif($tmp == 6) {
    $qarg->{'sort'} = "URL-ASC";
} else {
    $qarg->{'sort'} = "NONE";
}

printout("alt属性の文字をインデックスに含めますか？\n");
printout("[1] 含める\n");
printout("[0] 含めない\n");
printout("どれにしますか？[0〜1] > ");
$tmp = <STDIN>;
chomp($tmp);
if($tmp == 1) {
    $qarg->{'rescuealt'} = "1";
}

if(argtest() <= 0) {
    printout("入力が変です。\n");
    exit;
}

### インデックス作成
makeindex();

### 終了
exit;

###############################
### genindex.plに個有の関数 ###
###############################

###
### 引数のテスト
###
sub argtest {
    return(-1) if($qarg->{'includedir'} eq "");
    return(-2) if($qarg->{'includeurl'} eq "");
    return(-3) if($qarg->{'suffix'} eq "");

    return(1);
}

###
### 出力関数
###
sub printout {
    my $str = $_[0];		# 文字列(引数)

    if($kanji eq "EUC") {
	# EUCの場合
	print $str;
    } elsif($kanji eq "JIS") {
	# JISの場合
	&jcode::convert(\$str,"jis");
	print $str;
    } else {
	# SJISの場合
	&jcode::convert(\$str,"sjis");
	print $str;
    }
}

