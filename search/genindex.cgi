#!/usr/local/bin/perl
#=============================================================================#
#                                                                             #
#                        msearch - mat's search program                       #
#                                 version 1.50                                #
#                                                                             #
#                  超簡易インデックス版検索エンジンプログラム                 #
#       Copyright (C) 2000-2003, Katsushi Matsuda. All Right Reserved.        #
#                                                                             #
#=============================================================================#

#=============================================================================#
#                             インデックス作成CGI                             #
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

### インデックスを作成する時のパスワードを設定して下さい．
$g_password = "0585gori";

$g_index = "default";           # デフォルトインデックス名
$body_background = "";		# 背景の画像
$body_bgcolor = "white";	# 背景の色
$body_text = "black";		# 文字の色
$body_link = "blue";		# 未到達リンクの色
$body_alink = "red";		# 活動中リンクの色
$body_vlink = "blue";		# 到達済リンクの色
$title_generate = "msearch / genindex / インデックス作成フォーム";
$title_control = "msearch / genindex / インデックス管理メニュー";
$title_result = "msearch / genindex / 実行";
$g_cgi = "genindex.cgi";	# このCGIプログラム
$g_cookie = "1";		# クッキーを使うか
$g_cookie_span = "60";		# クッキーの有効期限(日数)

##################
### メイン処理 ###
##################

### 引数の取得とパージング
$arg = getargument();
$qarg = parseargument($arg);

### クッキーの取得とパージング
$chash = parsecookie() if($g_cookie == 1);

### バッファリングの停止
$io = select(STDOUT);
$| = 1;
select($io);

### モード選択
if($qarg->{'mode'} eq "control") {
    ### インデックス補助ツールモード
    if($qarg->{'action'} ne "") {
	## 補助ツールコマンド実行(クッキーは出力しない)
	# HTMLのContent-typeを出力する
	printcontenttype();
	# ヘッダーの出力
	printheader($title_result);
	# パスワードのチェック
	if(checkpassword() != 1) {
	    print "<font color=red>パスワードが違います</font>\n";
	    exit;
	}
	## 各アクションによって処理を分岐 
	if($qarg->{'action'} eq "get") {
	    ## 情報取得
	    doget();
	} elsif($qarg->{'action'} eq "delete") {
	    ## インデックス削除
	    dodelete();
	} elsif($qarg->{'action'} eq "make") {
	    ## 空インデックス作成
	    domake();
	} elsif($qarg->{'action'} eq "combine") {
	    ## インデックス結合
	    docombine();
	} else {
	    ## 不明なアクション
	}
	# フッターの出力
	printfooter();
    } else {
	## 補助ツール画面(クッキーは出力しない)
	# HTMLのContent-typeを出力する
	printcontenttype();
	# ヘッダーの出力
	printheader($title_control);
	# 補助ツールの出力
	printmenu();
	# フッターの出力
	printfooter();
    }
} else {
    ## インデックス作成モード
    if($qarg->{'includedir'} ne "" && $qarg->{'includeurl'} ne "" &&
       $qarg->{'conf'} ne "") {
	## インデックス作成(クッキーは出力する)
	# デバッグモードのチェック
	if($qarg->{'debug'} ne "") {
	    $debug = $qarg->{'debug'};
	}
	# $qarg->{'rescuealt'}はindexing.plで直接参照する
	# クッキーを出力する
	printallcookie() if($g_cookie == 1);
	# HTMLのContent-typeを出力する
	printcontenttype();
	# ヘッダーの出力
	printheader($title_result);
	# パスワードのチェック
	if(checkpassword() != 1) {
	    print "<font color=red>パスワードが違います</font>\n";
	    exit;
	}
	# インデックス作成呼び出し
	makeindex();
	# フッターの出力
	printfooter();
    } else {
	## インデックス作成画面(クッキーは出力しない)
	# HTMLのContent-typeを出力する
	printcontenttype();
	# ヘッダーの出力
	printheader($title_generate);
	# 作成フォームの出力
	printform();
	# フッターの出力
	printfooter();
    }
}

### 終了
exit;

################################
### genindex.cgiに個有の関数 ###
################################

###
### 引数の取得
###
sub getargument {
	my $arg;	# 取得するクエリー(戻り値)

	if($ENV{'REQUEST_METHOD'} eq 'GET') {
		$arg = $ENV{'QUERY_STRING'};
	} elsif ($ENV{'REQUEST_METHOD'} eq 'POST') {
		read(STDIN,$arg,$ENV{'CONTENT_LENGTH'});
	}

	return $arg;
}

###
### 引数のパーズ
###
sub parseargument {
	my $arg = $_[0];	# エンコードされた引数(引数)
	my %qarg;		# パーズ結果のハッシュ(戻り値)
	my @avpairs;	# 属性-値ペアの配列
	my $avpair;	# 属性-値ペア
	my $attribute;	# 属性
	my $value;	# 値

	@avpairs = split(/&/,$arg);
	for $avpair (@avpairs) {
		# 空白のデコード
		$avpair =~ tr/+/ /;
		# 属性と値に分解
		($attribute,$value) = split(/=/,$avpair);
		# 属性のデコード
		$attribute =~ s/%([\da-fA-F]{2})/pack("C",hex($1))/ge;
		# 値のデコード
		$value =~ s/%([\da-fA-F]{2})/pack("C",hex($1))/ge;
		$value =~ s/ //g;
		# 同じ属性が複数ある場合は','で繋ぐ
		if(defined $qarg{$attribute}) {
			$qarg{$attribute} .= ",$value";
		} else {
			$qarg{$attribute} = $value;
		}
	}
	return \%qarg;
}

###
### クッキーのパーズ
###
sub parsecookie {
    my %cookies;		# パーズ結果のハッシュ(戻り値)
    my @avpairs;		# 属性-値ペアの配列
    my $avpair;			# 属性-値ペア
    my $attribute;		# 属性
    my $value;			# 値

    @avpairs = split(/; /,$ENV{'HTTP_COOKIE'});
    for $avpair (@avpairs) {
	# 属性と値に分解
	($attribute,$value) = split(/=/,$avpair);
	# 空白のデコード
	$value =~ tr/+/ /;
	# 値のデコード
	$value =~ s/%([\da-fA-F]{2})/pack("C",hex($1))/ge;
	$cookies{$attribute} = $value;
    }
    return \%cookies;
}

###
### パスワードのチェック
###
sub checkpassword {
    my $t_pass = "";

    if($qarg->{'conf'} ne "") {
	$t_pass = $qarg->{'conf'};
	&jcode::convert(\$t_pass,"euc","","");
	if($g_password eq $t_pass) {
	    # パスワードが合っている
	    return(1);
	} else {
	    # パスワードが違っている
	    return(0);
	}
    } else {
	# パスワードが違っている
	return(0);
    }
}

###
### 全てのクッキーを出力する
###
sub printallcookie {
    if($qarg->{'index'} ne "") {
	printcookie('index',$qarg->{'index'},$g_cookie_span);
    }
    if($qarg->{'includedir'} ne "") {
	printcookie('includedir',$qarg->{'includedir'},$g_cookie_span);
    }
    if($qarg->{'includeurl'} ne "") {
	printcookie('includeurl',$qarg->{'includeurl'},$g_cookie_span);
    }
    if($qarg->{'suffix'} ne "") {
	printcookie('suffix',$qarg->{'suffix'},$g_cookie_span);
    }
    if($qarg->{'excludedir'} ne "") {
	printcookie('excludedir',$qarg->{'excludedir'},$g_cookie_span);
    }
    if($qarg->{'excludefile'} ne "") {
	printcookie('excludefile',$qarg->{'excludefile'},$g_cookie_span);
    }
    if($qarg->{'excludekey'} ne "") {
	printcookie('excludekey',$qarg->{'excludekey'},$g_cookie_span);
    }
    if($qarg->{'sort'} ne "") {
	printcookie('sort',$qarg->{'sort'},$g_cookie_span);
    }
    if($qarg->{'rescuealt'} ne "") {
	printcookie('rescuealt',$qarg->{'rescuealt'},$g_cookie_span);
    }
}

###
### クッキーの出力
###
sub printcookie {
    my $attribute = $_[0];	# 属性名(入力)
    my $value = $_[1];		# 値(入力)
    my $timespan = $_[2];	# expireまでの時間(単位=日)(入力)
    my @week = ("Sun","Mon","Tue","Wed","Thu","Fri","Sat");
    my @month = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec");
    my ($sec,$min,$hour,$day,$mon,$year,$wday);

    # 値のエンコーディング
    $value =~ s/(\W)/sprintf("%%%02X", unpack("C", $1))/ge;
    # expire日の作成
    ($sec,$min,$hour,$day,$mon,$year) = gmtime();
    $year += 1900;
    plusday(\$year,\$mon,\$day,$timespan); # 何日後の計算
    $wday = $week[&dayweek($year,$mon,$day)]; # 曜日の計算
    $mon = $month[$mon];
    $hour = "0" . $hour if($hour < 10);
    $min = "0" . $min if($min < 10);
    $sec = "0" . $sec if($sec < 10);

    # 出力
    print "Set-Cookie: $attribute=$value; ";
    print "expires=$wday, $day-$mon-$year $hour:$min:$sec GMT;\n";
}

###
### 曜日を返す関数
###
sub dayweek {
    my $year = $_[0];		# 年(入力)
    my $month = $_[1];		# 月(入力) [0....11]
    my $day = $_[2];		# 日(入力)
    my $dayweek;		# 曜日(戻り値) [0...6]

    $month++;
    if($month < 3) {
	$year--;
	$month += 12;
    }
    $dayweek = ($year + $year/4 - $year/100 + $year/400 +
		(13 * $month + 8)/5 + $day) % 7;
    return($dayweek);
}

###
### うるう年がどうかを返す関数(1:閏年，0:平年)
###
sub isuruu {
    my $year = $_[0];		# 年(入力)

    if(($year%4) == 0) {
	if(($year%400) == 0) {
	    return(1);
	} elsif(($year%100) == 0) {
	    return(0);
	} else {
	    return(1);
	}
    } else {
	return(0);
    }
}

###
### ある日から何日後を計算する
###
sub plusday {
    my $year = $_[0];		# 年への参照(入力)
    my $month = $_[1];		# 月への参照(入力) [0....11]
    my $day = $_[2];		# 日への参照(入力)
    my $span = $_[3];		# 足す日(入力)
    my @mday = (31,28,31,30,31,30,31,31,30,31,30,31);

    while($span > 0) {
	my $thismonth = $mday[$$month];	# 現在の月の最終日
	$mday[1] += 1 if($$month == 1 && isuruu($$year) == 1); # うるう年の2月

	if($thismonth - $$day < $span) {
	    # 次の月へ
	    $span -= $thismonth - $$day + 1;
	    $$day = 1;
	    $$month++;
	    if($$month > 11) {
		# 次の年へ
		$$month = 0;
		$$year++;
	    }
	} else {
	    # この月で全部足せた
	    $$day += $span;
	    $span = 0;
	}
    }
}

###
### 情報取得
###
sub doget {
    my @files = ();
    my $file = "";

    print "<font color=blue>補助ツールモードへは，ブラウザの「戻る」で戻って下さい．</font><p>\n";
    print "<b>SERVER_NAME</b> = $ENV{SERVER_NAME}<br>\n";
    print "<b>HTTP_HOST</b> = $ENV{HTTP_HOST}<br>\n";
    print "<b>SERVER_SOFTWARE</b> = $ENV{SERVER_SOFTWARE}<br>\n";
    print "<b>DOCUMENT_ROOT</b> = $ENV{DOCUMENT_ROOT}<br>\n";
    print "<b>SCRIPT_FILENAME</b> = $ENV{SCRIPT_FILENAME}<br>\n";
    print "<b>SCRIPT_NAME</b> = $ENV{SCRIPT_NAME}<br>\n";
    if(exists $ENV{MOD_PERL}) {
	print "<b>MOD_PERL VERSION</b> = $ENV{MOD_PERL}<br>\n";
    } else {
	print "<b>PERL VERSION</b> = $]<br>\n";
    }
    print "<b>PROCESS ID</b> = $$<br>\n";
    print "<b>REAL USER ID</b> = $<(" . user($<) . ")<br>\n";
    print "<b>EFFECTIVE USER ID</b> = $>(" . user($>) . ")<br>\n";
    print "<b>REAL GROUP ID</b> = $( " . group($() . "<br>\n";
    print "<b>EFFECTIVE GROUP ID</b> = $) " . group($)) . "<br>\n";
    print "<b>HTTP_USER_AGENT</b> = $ENV{HTTP_USER_AGENT}<br>\n";
    print "<b>CURRENT DIR</b> = " . mypwd() . "<br>\n";
    print "<p>\n";
    print "<table border=1 cellspacing=0 cellpadding=0 cols=1><tr><td>\n";
    print "<table border=0 cols=2>\n";
    print "<tr><th>index name</th><th>file name</th></tr>\n";
    opendir(P,".");
    @files = readdir(P);
    closedir(P);
    foreach $file (@files) {
	if($file =~ /\.idx$/i) {
	    my $i = $file;
	    $i =~ s/\.idx$//i;
	    print "<tr><td>$i</td><td>$file</td>\n";
	}
    }
    print "</table></td></tr></table>\n";
    print "<p>\n";
    print "<table border=1 cellspacing=0 cellpadding=0 cols=1><tr><td>\n";
    print "<table border=0 cols=6>\n";
    print "<tr><th>mode</th><th>user</th><th>group</th>";
    print "<th>size</th><th>last modified</th><th>file name</th></tr>\n";
    foreach $file (@files) {
	my @tmp = stat("./$file");
	print "<tr>\n";
	print "<td>" . getmode("./$file",$tmp[2]) . "</td>\n";
	print "<td>" . user($tmp[4]) . "</td>\n";
	print "<td>" . group($tmp[5]) . "</td>\n";
	print "<td align=right>$tmp[7]</td>\n";
	print "<td>" . formattime($tmp[9]) . "</td>\n";
	print "<td>$file</td>\n";
	print "</tr>\n";
    }
    print "</table></td></tr></table>\n";
}

###
### インデックス削除
###
sub dodelete {
    my $index = $qarg->{'index'};
    my $file = "";

    print "<font color=blue>補助ツールモードへは，ブラウザの「戻る」で戻って下さい．</font><p>\n";

    $index = $g_index if($index eq "");
    $file = $index . ".idx";
    if(unlink($file)) {
	print "インデックス:$indexを削除しました．";
    } else {
	print "インデックス:$indexを削除するのに失敗しました．";
    }
}

###
### 空インデックス作成
###
sub domake {
    my $index = $qarg->{'index'};
    my $file = "";

    print "<font color=blue>補助ツールモードへは，ブラウザの「戻る」で戻って下さい．</font><p>\n";

    $index = $g_index if($index eq "");
    $file = $index . ".idx";

    # try 1
    if(open(FILE,">$file")) {
	print "空インデックス:$indexを作成しました．(try 1)";
	close(FILE);
	return;
    }
    # try 2
    if(sysopen(FILE,"$file",O_RDWR|O_CREAT)) {
	print "空インデックス:$indexを作成しました．(try 2)";
	close(FILE);
	return;
    }
    # try 3
    `touch $file`;
    if(-f $file && -z $file) {
	print "空インデックス:$indexを作成しました．(try 3)";
	return;
    }

    print "空インデックスの作成に失敗しました．";
}

###
### インデックス結合
###
sub docombine {
    my @files = ();
    my @indice = ();
    my ($file, $all);

    print "<font color=blue>補助ツールモードへは，ブラウザの「戻る」で戻って下さい．</font><p>\n";

    unlink("./$g_index.idx");
    opendir(P,".");
    @files = readdir(P);
    closedir(P);
    foreach $file (@files) {
	if($file =~ /\.idx$/i) {
	    push(@indice,$file);
	}
    }
    if($#indice == -1) {
	print "インデックス結合に失敗しました(結合対象のインデックスが存在しません)．";
	return;
    }

    # try 1
    $all = join(" ",@indice);
    `cat $all>./$g_index.idx`;
    if(-f "./$g_index.idx" && -s "./$g_index.idx") {
	print "インデックス結合に成功しました．(try 1)";
	return;
    }

    # try 2
    if(!open(FILE,">./$g_index.idx")) {
	print "インデックス結合に失敗しました($g_indexインデックス作成失敗)．";
	return;
    }
    foreach $file (@indice) {
	if(!open(IN,"<$file")) {
	    print "インデックス結合に失敗しました($fileインデックスオープンエラー)．";
	    return;
	}
	while(<IN>) {
	    print FILE $_;
	}
	close(IN);
    }
    close(FILE);
    if(-f "./$g_index.idx" && -s "./$g_index.idx") {
	print "インデックス結合に成功しました．(try 2)";
	return;
    } else {
	print "インデックス結合に失敗しました($g_indexインデックス書き込みエラー)．";
	return;
    }
}

###
### ファイル名とモードから-rwxr-xr-xみたいな文字列を返す
###
sub getmode {
    my $filename = $_[0];
    my $mode = $_[1];

    if(-d $filename) {
	$str = "d";
    } elsif(-l $filename) {
	$str = "l";
    } else {
	$str = "-";
    }

    if($mode & 0400) {
	$str .= "r";
    } else {
	$str .= "-";
    }
    if($mode & 0200) {
	$str .= "w";
    } else {
	$str .= "-";
    }
    if($mode & 0100) {
	$str .= "x";
    } else {
	$str .= "-";
    }
    if($mode & 040) {
	$str .= "r";
    } else {
	$str .= "-";
    }
    if($mode & 020) {
	$str .= "w";
    } else {
	$str .= "-";
    }
    if($mode & 010) {
	$str .= "x";
    } else {
	$str .= "-";
    }
    if($mode & 04) {
	$str .= "r";
    } else {
	$str .= "-";
    }
    if($mode & 02) {
	$str .= "w";
    } else {
	$str .= "-";
    }
    if($mode & 01) {
	$str .= "x";
    } else {
	$str .= "-";
    }

    return($str);
}

###
### uidからユーザ名を返す
###
sub user {
    return( (getpwuid($_[0]))[0] );
}

###
### gidからグループ名を返す
###
sub group {
    return( (getgrgid($_[0]))[0] );
}

###
### 日時をフォーマットする
###
sub formattime {
    my ($s,$m,$h,$d,$mon,$year);

    ($s,$m,$h,$d,$mon,$year) = localtime($_[0]);
    $year += 1900;
    $month += 1;
    $s = "0$s" if($s < 10);
    $m = "0$m" if($m < 10);
    $h = "0$h" if($h < 10);
    $d = "0$d" if($d < 10);
    $mon = "0$mon" if($mon < 10);

    return("$year年$mon月$d日 $h:$m");
}

###
### カレントディレクトリのパスを取得
###
sub mypwd {
    my @dirname = ();
    my ($p, $pi);
    my @stat;
    my $c = ".";
    my @cstat = stat($c);
    my $ci = $cstat[1];
    my $pwd = "";
    while(1) {
	$p = "$c/..";
	@stat = stat($p);
	$pi = $stat[1];
	opendir(P,"$p");
	@files = readdir(P);
	closedir(P);
	foreach $file (@files) {
	    next if($file eq "." || $file eq "..");
	    @stat = stat("$p/$file");
	    if($stat[1] eq $ci) {
		if($stat[0] eq $cstat[0]) {
		    push(@dirname,$file);
		}
	    }
	}
	if($pi eq $ci) {
	    foreach (@dirname) {
		$pwd = "/$_$pwd";
	    }
	    return($pwd);
	}
	$c = $p;
	$ci = $pi;
    }
}

###
### HTML Content-type出力
###
sub printcontenttype {
	print "Content-type: text/html\n\n";
}

###
### HTMLヘッダーの出力
###
sub printheader {
    my $title = $_[0];		# タイトル(引数)
    my $body_attr = "";		# bodyタグの属性

    print "<html>\n";
    print "<header>\n";
    print "<meta http-equiv=\"Content-Type\" content=\"text/html;charset=x-euc-jp\">\n";
    print "<meta http-equiv=\"Content-Language\" content=\"jp\">\n";
    print "<title>$title</title>\n";
    print "</header>\n";
    $body_attr .= " background=\"$body_background\"" if $body_background;
    $body_attr .= " bgcolor=\"$body_bgcolor\"" if $body_bgcolor;
    $body_attr .= " text=\"$body_text\"" if $body_text;
    $body_attr .= " link=\"$body_link\"" if $body_link;
    $body_attr .= " alink=\"$body_alink\"" if $body_alink;
    $body_attr .= " vlink=\"$body_vlink\"" if $body_vlink;
    print "<body $body_attr>\n";
}

###
### HTMLフッターーの出力
###
sub printfooter {
    print "</body>\n";
    print "</html>\n";
}

###
### 作成フォームの出力
###
sub printform {
    my $c_includedir = "";
    my $c_includeurl = "";
    my $c_suffix = "";
    my $c_excludedir = "";
    my $c_excludefile = "";
    my $c_excludekey = "";

    if($g_cookie == 1) {
	$c_index = $chash->{'index'};
	$c_includedir = $chash->{'includedir'};
	$c_includeurl = $chash->{'includeurl'};
	$c_suffix = $chash->{'suffix'};
	$c_excludedir = $chash->{'excludedir'};
	$c_excludefile = $chash->{'excludefile'};
	$c_excludekey = $chash->{'excludekey'};
	if($chash->{'sort'} eq "NONE") {
	    $s_nn = "selected";
	} elsif($chash->{'sort'} eq "MODIFY-DESC") {
	    $s_md = "selected";
	} elsif($chash->{'sort'} eq "MODIFY-ASC") {
	    $s_ma = "selected";
	} elsif($chash->{'sort'} eq "TITLE-DESC") {
	    $s_td = "selected";
	} elsif($chash->{'sort'} eq "TITLE-ASC") {
	    $s_ta = "selected";
	} elsif($chash->{'sort'} eq "URL-DESC") {
	    $s_ud = "selected";
	} elsif($chash->{'sort'} eq "URL-ASC") {
	    $s_ua = "selected";
	}
	if($chash->{'rescuealt'} eq "1") {
	    $s_rescue = "selected";
	} else {
	    $s_notrescue = "selected";
	}
    }

    print <<HERE_DOC;
<center>
<h3>
msearch用インデックス作成フォーム
　　　
<a href="$g_cgi?mode=control">msearch用インデックス補助ツール</a>
</h3>
</center>
<p>
<center>
<form action="$g_cgi" method="post" accept-charset="x-euc-jp">
<table border=1>
<tr>
<td>インデックス名<sup>※1</sup></td>
<td><input type="text" name="index" value="$c_index" size=50></td>
</tr>
<tr>
<td>対象ディレクトリ<sup>※2</sup><font color=blue>(必須)</font></td>
<td><input type="text" name="includedir" value="$c_includedir" size=50></td>
</tr>
<tr>
<td>対象ディレクトリのURL<sup>※3</sup><font color=blue>(必須)</font></td>
<td><input type="text" name="includeurl" value="$c_includeurl" size=50></td>
</tr>
<tr>
<td>対象ファイルの拡張子<sup>※4</sup></td>
<td><input type="text" name="suffix" value="$c_suffix" size=50></td>
</tr>
<tr>
<td>非対象ディレクトリ<sup>※5</sup></td>
<td><input type="text" name="excludedir" value="$c_excludedir" size=50></td>
</tr>
<tr>
<td>非対象ファイル<sup>※6</sup></td>
<td><input type="text" name="excludefile" value="$c_excludefile" size=50></td>
</tr>
<tr>
<td>非対象キーワード<sup>※7</sup></td>
<td><input type="text" name="excludekey" value="$c_excludekey" size=50></td>
</tr>
<tr>
<td>ランキング方法<sup>※8</sup></td>
<td>
<select name="sort">
<option value="NONE" $s_nn>ランキングなし
<option value="MODIFY-DESC" $s_md>最終更新日時-降順
<option value="MODIFY-ASC" $s_ma>最終更新日時-昇順
<option value="TITLE-DESC" $s_td>タイトル-降順
<option value="TITLE-ASC" $s_ta>タイトル-昇順
<option value="URL-DESC" $s_ud>URL-降順
<option value="URL-ASC" $s_ua>URL-昇順
</select></td>
</tr>
<tr>
<td>alt文字の追加<sup>※9</sup></td>
<td>
<select name="rescuealt">
<option value="1" $s_rescue>追加する
<option value="0" $s_notrescue>追加しない
</select></td>
</tr>
<tr>
<td>パスワード<sup>※10</sup><font color=blue>(必須)</font></td>
<td><input type="password" name="conf" value="" size=50>
</tr>
<tr>
<td colspan=2 align=right>
<input type="checkbox" name="debug" value="1">
デバッグモード<sup>※11</sup>　　
<input type="submit" value="インデックス作成">
</td>
</tr>
</table>
</form>
<p>
<table border=0 width=80%>
<tr>
<td nowrap=true valign=top><small>※1</small></td>
<td><small>作成するインデックスの名称．指定しない場合はデフォルト値(default)
    が名称となる．インデックスを切り替えて検索する場合には，それぞれの検索
    対象毎にインデックスの名称を付ける．インデックスのファイル名は
    インデックス名に『.idx』という拡張子(suffix)が自動的に付けられるので，
    ここでは拡張子を指定してはならない．</small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※2</small></td>
<td><small>インデックス化するHTMLファイルがあるディレクトリ．必ず1ディレクト
    リのみ指定しなければならない．絶対パスではなく，このプログラム
    (genindex.cgi)のあるディレクトリからの相対パスもしくは，絶対パスで指定
    する．このプログラムは，この指定されたディレクトリ以下のすべてのHTML
    ファイルをインデックス化する．</small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※3</small></td>
<td><small>上の対象ディレクトリがURLでは表されるかを指定する．例えば，対象
    ディレクトリが，"../public_html"であり，そのURLが
    "http://www.foo.co.jp/~user/"の様に指定する．</small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※4</small></td>
<td><small>インデックス化するHTMLファイルの拡張子を指定する．何も指定しない
    場合は，".html"と".htm"．指定する場合は，このデフォルト値を上書きするの
    で，注意が必要．".html,.shtml"の様に半角のカンマを使い，複数指定できる
    (実際にはダブルクォーテーションはいらない)．</small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※5</small></td>
<td><small>上の対象ディレクトリの中でインデックス化しないディレクトリを指定
    する．例えば，"../public_html/cgi-bin"以下をインデックス化しない場合は，
    "cgi-bin"の様に対象ディレクトリからの相対パスで指定する．半角カンマを
    使い，複数指定できる．<br>また，非対象ディレクトリにしたいディレクトリ
    名を正規表現を使って指定することができる．ただし，この場合，対象ディレ
    クトリからの相対パスではなく，ディレクトリ名のみを正規表現で指定する．
    例えば，対象ディレクトリ以下にある全ての"_vti_cnf"というディレクトリを
    インデックス化したくない場合は"(_vti_cnf)"とする．"("と")"は，この中は
    正規表現だと指定するために必要です．"(_vti_cnf)"の代わりに"(^_.*)"の
    ように記述しても構いません．</small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※6</small></td>
<td><small>上の対象ディレクトリの中で，且つ非対象ディレクトリ以外でインデッ
    クス化しないファイルを指定する．例えば，"../public_html/secret.html"
    ファイルをインデックス化したくない場合は，"secret.html"の様に対象ディレ
    クトリからの相対パスで指定する．半角カンマを使い，複数指定できる．<br>
    また，非対象ディレクトリと同様に非対象ファイルとしたいファイル名を正規
    表現を使って指定することができる．正規表現は"("と")"で囲って指定する．
    </small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※7</small></td>
<td><small>検索対象に入れたくないキーワードを指定します．ここで指定したキー
    ワードで検索した場合，検索結果は0件となります．半角カンマを使い，複数
    指定できます．例えば，「インターネット」と「検索」というキーワードを
    検索対象にしたくない場合は，"インターネット,検索"と指定します．ここで
    指定したキーワードは検索結果の一部表示にも出てきませんので注意して下さい．
    ただし，タイトルに含まれるキーワードは削除しません．</small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※8</small></td>
<td><small>検索結果のランキング(ソート)方法を指定します．ランキングはイン
    デックスを作る時に決定しなければなりません．</small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※9</small></td>
<td><small>ここをチェックすると，alt属性中の文字列も検索対象に含めます．
    </small></td>
</tr>
<tr>
<td nowrap=true valign=top><small>※10</small></td>
<td><small>このCGIを動かすことが出来る人を限定するためのパスワードです．生
    のパスワードデータを送りますので，グラブされる可能性があります．</small>
    </td>
</tr>
<tr>
<td nowrap=true valign=top><small>※11</small></td>
<td><small>ここをチェックすると，デバッグ情報が出力されます．正常に
    インデックスが作成されない場合の状況を把握するために有益な情報が表示
    されます．</small></td>
</tr>
</table>
</center>
HERE_DOC
}

###
### 補助ツールの出力
###
sub printmenu {
    print <<HERE_DOC;
<center>
<h3>
<a href="$g_cgi?mode=generate">msearch用インデックス作成フォーム</a>
　　　
msearch用インデックス補助ツール
</h3>
</center>
<p>
<center>

<form action="$g_cgi" method="post" accept-charset="x-euc-jp">
<table border=1 cols=2>
<tr>
<td colspan=2 align=center><b>各種情報の取得</b></td>
<tr>
<td>パスワード<font color=blue>(必須)</font></td>
<td><input type="password" name="conf" value="" size=50></td>
</tr>
<tr>
<td colspan=2 align=right><input type="submit" value="情報取得"></td>
</tr>
</table>
<input type="hidden" name="mode" value="control">
<input type="hidden" name="action" value="get">
<table border=0 width=50%>
<tr><td>
<font size=-1>インデックスを含むmsearch関連のファイル情報，CGIの実行情報，
ディレクトリ情報などを取得します．</font><br>
<font size=-1 color=red>
セキュリティ上危険な情報も取得しますので，ご注意．</font><br>
</td></tr>
</table>
</form>

<p>

<form action="$g_cgi" method="post" accept-charset="x-euc-jp">
<table border=1 cols=2>
<tr>
<td colspan=2 align=center><b>インデックスの削除</b></td>
<tr>
<td>インデックス名</td>
<td><input type="text" name="index" value="" size=50></td>
</tr>
<tr>
<td>パスワード<font color=blue>(必須)</font></td>
<td><input type="password" name="conf" value="" size=50></td>
</tr>
<tr>
<td colspan=2 align=right><input type="submit" value="インデックス削除"></td>
</tr>
</table>
<input type="hidden" name="mode" value="control">
<input type="hidden" name="action" value="delete">
<table border=0 width=50%>
<tr><td>
<font size=-1>インデックス対象ファイルの変更がなく，インデックスを作り直し
たい場合(ランキング方法を変更，alt文字の追加，非対象キーワードの追加等)や，
インデックスに互換性がある時のmsearchのバージョンアップ時には，インデックス
を削除して，新たにインデックスを作成して下さい．
genindex.cgiのインデックス更新処理はインデックス対象ファイルの更新日時のみ
を見ています．</font>
<br>
<font size=-1 color=red>インデックス名に何も指定しないと，デフォルトの
インデックス(default)が削除対象となります．
拡張子(.idx)は付けないで下さい．</font>
</td></tr>
</table>
</form>

<p>

<form action="$g_cgi" method="post" accept-charset="x-euc-jp">
<table border=1 cols=2>
<tr>
<td colspan=2 align=center><b>空インデックスの作成</b></td>
<tr>
<td>インデックス名</td>
<td><input type="text" name="index" value="" size=50></td>
</tr>
<tr>
<td>パスワード<font color=blue>(必須)</font></td>
<td><input type="password" name="conf" value="" size=50></td>
</tr>
<tr>
<td colspan=2 align=right><input type="submit" value="空インデックス作成"></td>
</tr>
</table>
<input type="hidden" name="mode" value="control">
<input type="hidden" name="action" value="make">
<table border=0 width=50%>
<tr><td>
<font size=-1>何らかの原因で，インデックスが作成できない場合は，
空のインデックスを作ってみて下さい．</font><br>
<font size=-1 color=red>
指定されたインデックス(指定されなかった場合はデフォルトインデックス(default))
が既に存在する場合は，そのインデックスが空になります．ご注意．
拡張子(.idx)は付けないで下さい．</font><br>
<font size=-1>基本的に，genindex.cgiでインデックスが作れない場合は，
このコマンドでも空インデックスが作れない可能性が高いです．
少し違った作成方法を試してみていますが，あまり期待しないで下さい．
</font>
</td></tr>
</table>
</form>

<p>

<form action="$g_cgi" method="post" accept-charset="x-euc-jp">
<table border=1 cols=2>
<tr>
<td colspan=2 align=center><b>インデックスの結合</b></td>
<tr>
<td>パスワード<font color=blue>(必須)</font></td>
<td><input type="password" name="conf" value="" size=50></td>
</tr>
<tr>
<td colspan=2 align=right><input type="submit" value="インデックス結合"></td>
</tr>
</table>
<input type="hidden" name="mode" value="control">
<input type="hidden" name="action" value="combine">
<table border=0 width=50%>
<tr><td>
<font size=-1>デフォルトインデックス(default)以外のインデックスを結合し，
デフォルトインデックス(default)を作ります．
インデックス対象ファイルが多すぎて，メモリ不足でgenindex.cgiが動作しない
場合は，サブディレクトリ単位等で小さなインデックスを作り，結合してみて
下さい．</font><br>
<font size=-1 color=red>
既存のデフォルトインデックスが既に存在する場合は，上書きされます．ご注意．<br>
また，結合元のインデックスは削除されません．
</font><br>
</td></tr>
</table>
</form>

</center>
HERE_DOC
}

###
### 出力関数
###
sub printout {
    my $str = $_[0];             # 文字列(引数)

    $str =~ s/\n/<br>/g;
    print "$str\n";
}

