#!/usr/local/bin/perl
#=============================================================================#
#                                                                             #
#                        msearch - mat's search program                       #
#                                 version 1.50                                #
#                                                                             #
#                  超簡易インデックス版検索エンジンプログラム                 #
#        Copyright (C) 2000-2003, Katsushi Matsuda. All Right Reserved.       #
#                                                                             #
#=============================================================================#

#=============================================================================#
#                                    検索CGI                                  #
#=============================================================================#

require './jcode.pl';		# 漢字コード変換パッケージ
require './fold.pl';		# ２バイト文字フォールディングパッケージ

########################################
### 各種変数定義(変更しないで下さい) ###
########################################

### インデックス関連
@g_index = ();			# インデックスの配列
				# ファイル名,URL,最終更新時刻,タイトル,中身
@match = ();			# 検索に引っかかったインデックス
				# ファイル名,URL,最終更新時刻,タイトル,一部
$g_indexfile = "";              # インデックスファイル

### クエリー関連
@g_and = ();			# 検索キーワード(and)
@g_not = ();			# 検索キーワード(not)
@g_or = ();			# 検索キーワード(or)
@g_title = ();			# 検索キーワード(title)
@g_url = ();			# 検索キーワード(url)
@g_and_i = ();			# 検索キーワード付帯情報(and)
@g_not_i = ();			# 検索キーワード付帯情報(not)
@g_or_i = ();			# 検索キーワード付帯情報(or)
@g_title_i = ();		# 検索キーワード付帯情報(title)
				# 付帯情報：1 含半角英文字
				# 　　　　　2 全角１文字
				# 　　　　　0 なし

### 設定ファイル関連
$g_config = "";                 # 設定ファイル
$f_home = "";                   # ホームページURL
$f_highlight = 1;               # ハイライトするかどうか
$f_highlight_deco = "<b>";      # ハイライトの方法
$f_tzdiff = 0;                  # サーバマシンとの時差
$f_notitle = "タイトルなし";    # タイトルなしの場合の表示方法
$f_log = 0;                     # ログを出力するかどうか
$f_logfile = "./msearch.log";   # ログのファイル名
$f_logencoding = "euc-jp";      # ログファイルの漢字コード
$f_logformat = "date remote\n    ua\n    hit件 query\n"; # ログ書式
$g_lock = "mslock";             # ロックディレクトリ名
$f_dateformat = "year年month月day日 hour時minute分second秒"; # 日時表示書式
$f_encoding = "euc-jp";         # HTML出力漢字コード
$f_extract_f = 40;              # 抽出文字数(前)
$f_extract_b = 160;             # 抽出文字数(後)

@f_page = ();                   # page
@f_pageindex = ();              # pageの書式インデックス
$f_result = "";                 # result
$f_result_num = 10;             # resultの繰り返し回数(=num)
$f_previous = "";               # previous
$f_next = "";                   # next
$f_pset = "";                   # pset
$f_pset_num = 5;                # psetの繰り返し回数
$f_cset = "";                   # cset
$f_nset = "";                   # nset
$f_nset_num = 5;                # nsetの繰り返し回数
$f_help = "";                   # help
$f_exist_indexnum = 0;          # helpフォーマット中でindexnumを使っているか

### フォーマット変数
$v_msearch = "msearch.cgi";     # cgi名
$v_home = "";                   # ホームページのURL
$v_query = "";                  # 現在の検索式
$v_index = "";                  # インデックス名
$v_config = "";                 # 設定ファイル名
$v_rpp = -1;                    # 1ページあたりの表示件数
$v_set = 1;                     # 現在の検索セット番号
$v_total = 0;                   # 検索結果総数
$v_from = 0;                    # 現在ページに表示される先頭件数
$v_to = 0;                      # 現在ページに表示される後尾件数
$v_cputime = (times)[0];        # かかった処理時間
$v_indexdate = "";              # インデックスの最終更新日時
$v_indexnum = 0;                # インデックスに登録されているページ総数
$v_nowdate = "";                # 現在日時
$v_msearchhp = "http://www.kiteya.net/script/msearch/"; # msearchの配布ページ
$v_version = "1.50";            # msearchのバージョン

### コード関連
$meta = '[\x24\x28-\x2B\x2D-\x2E\x3f\x5B-\x5E\x7B-\x7D]'; # メタキャラクタ
$han1 = '[\x00-\x7F]';		# EUC半角文字の正規表現
$hank = '\x8E[\xA0-\xDF]';	# EUC半角カタカナの正規表現
$zen2 = '[\x8E\xA1-\xFE][\xA1-\xFE]'; # EUC全角文字(2バイト)の正規表現
$zen3 = '\x8F[\xA1-\xFE][\xA1-\xFE]'; # EUC全角文字(3バイト)の正規表現
$peuc = '[\xA1-\xFE][\xA1-\xFE]'; # 全角１文字で問題となる2バイト文字
$feuc = "($hank|$zen2|$zen3)*($han1|\$)"; # 全角１文字に続く文字列の正規表現

##################
### メイン処理 ###
##################

$io = select(STDOUT);
$| = 1;
select($io);

### 引数の取得とパージング
$arg = getargument();
$qarg = parseargument($arg);

### 引数の値を変数代入
# 検索キーワード(query)
if($qarg->{'query'} ne "") {
    my $query = $qarg->{'query'};

    ## 検索式の保存
    &jcode::convert(\$query,"euc");
    $v_query = $query;

    ## クエリーのサニタライズ
    $query =~ s/</&lt;/g;
    $query =~ s/>/&gt;/g;

    ## クエリーの正規化
    normalize(\$query);

    ## キーワードの解釈
    # OR条件
    while(1) {
	if($query =~ s/\((.*?)\)//) {
	    my $tmp = $1;
	    $tmp =~ s/^,*//;
	    if($tmp =~ /,/) {
		z2h(\$tmp);
		push(@g_or,$tmp);
	    } else {
		z2h(\$tmp);
		push(@g_and,"($tmp)");
	    }
	} else {
	    last;
	}
    }
    $query =~ s/,+/,/g;
    $query =~ s/^,//;
    $foo = $query;
    my @keywords = split(/,/,$query); # すべてのキーワード
    while(@keywords) {
	my $key = shift(@keywords); # １つのキーワード
	if($key =~ /^"(.*)"$/) {
	    # and検索(クオートされた場合)
	    my $newkey = $1;
	    z2h(\$newkey);
	    push(@g_and,$newkey);
	} elsif($key =~ /^-(.*)$/) {
	    # not検索
	    my $newkey = $1;
	    z2h(\$newkey);
	    push(@g_not,$newkey);
	} elsif($key =~ /^[tT]:(.*)$/) {
	    # title検索
	    my $newkey = $1;
	    z2h(\$newkey);
	    push(@g_title,$newkey);
	} elsif($key =~ /^[uU]:(.*)$/) {
	    # url検索
	    push(@g_url,$1);
	} else {
	    # and検索
	    z2h(\$key);
	    push(@g_and,$key);
	}
    }
}

### 検索結果のセット数
if($qarg->{'set'} ne "") {
    $v_set = $qarg->{'set'};
    $v_set++;
    $v_set--;
    $v_set = 1 if($v_set eq "");
}

### HTMLのContent-typeを出力する
printcontenttype();

### 設定ファイルの確定
if($qarg->{'config'} ne "") {
    $g_config = "./" . $qarg->{'config'} . ".cfg";
    $v_config = $qarg->{'config'};
} else {
    if($qarg->{'index'} ne "") {
	my $tmp_config = "./" . $qarg->{'index'} . ".cfg";
	if(-e $tmp_config) {
	    $g_config = $tmp_config;
	} else {
	    $g_config = "./default.cfg";
	}
    } else {
	$g_config = "./default.cfg";
    }
}

### インデックスの確定
if($qarg->{'index'} eq "") {
    $g_indexfile = "./default.idx";
} else {
    $g_indexfile = "./" . $qarg->{'index'} . ".idx";
    $v_index = $qarg->{'index'};
}

### 設定ファイルの読み込み
parseconfig();
$v_home = $f_home;
$v_rpp = $f_result_num;

### 検索結果一覧表示数
if($qarg->{'num'} ne "") {
    # cgi引数にnumが指定されている場合はそれを優先する
    $v_rpp = $qarg->{'num'};
    $v_rpp++;
    $v_rpp--;
    $v_rpp = 10 if($v_rpp eq "");
}

### 現在日時の取得
$v_nowdate = getnowdate();

### インデックスの最終更新日時の取得
$v_indexdate = getindexdate();

### 引数があるかどうかを検索式でチェック
$tmp = @g_and + @g_not + @g_or + @g_title + @g_url;

###
### 引数なしで呼ばれた場合の処理
###
if($tmp == 0) {
    if($f_exist_indexnum == 1) {
	$v_indexnum = getindexnum();
    }
    getcputime();
    printhelp();
    exit;
}

###
### 引数ありの場合は以下
###

my ($i, $j, $hl_open, $hl_close);
my ($url, $title, $contents, $part);
my ($in, $flag, $d_start, $d_end);
my ($cgicall, $tset);

### 変な呼び出しのチェック
checkinvalid();

### ハイライトの閉じるタグの作成
$hl_open = $f_highlight_deco;
$hl_close = $f_highlight_deco;
$hl_close =~ s/<(.*?)[\s>].*$/<\/\1>/;

### インデックスを読み込む
$v_indexnum = readindex() if(-f $g_indexfile);
if($v_indexnum == 0) {
    printerror("インデックスがありません．");
}

### 表示開始番号(先頭件数-1)と表示終了番号(後尾件数-1)の計算
if($v_rpp == 0) {
    $d_start = 0;
    $d_end = $v_indexnum - 1;
} else {
    $d_start = ($v_set - 1) * $v_rpp;
    $d_end = $v_set * $v_rpp - 1;
}

### クエリ内のメタ文字のエスケープ
escapequery();

###
### 各検索キーワードでインデックスを検索
###
for($i=0;$i<$v_indexnum;$i++) {
    # 各パーツに分解
    ($url,undef,$title,$contents) = split(/\t/,$g_index[$i]);

    # 部分の初期化
    $part = "";

    # 範囲内かどうかを予め求めておく
    if($v_total >= $d_start && $v_total <= $d_end) {
	$in = 1;
    } else {
	$in = 0;
    }

    ### 各条件でチェック
    $flag = 1;		# まずはマッチしたと仮定する
    ### and条件
    if($flag == 1 && @g_and > 0) {
	for($j=0;$j<@g_and&&$flag==1;$j++) {
	    if($g_and_i[$j] == 0) {
		## 全角１文字以外の場合
		if($title =~ /$g_and[$j]/) {
		    # キーワードがあった(続ける)
		    next;
		} elsif($contents =~ /$g_and[$j]/) {
		    # キーワードがあった(続ける)
		    if($in == 1 && $part eq "") {
			$prev = $`;
			$self = $&;
			$next = $';
			$part = "1";
		    }
		    next;
		} else {
		    # キーワードがなかった(やめる)
		    $flag = 0;
		}
	    } else {
		## 全角１文字の場合
		if($title =~ /$g_and[$j]$feuc/) {
		    next;
		} elsif($contents =~ /$g_and[$j]$feuc/) {
		    if($in == 1 && $part eq "") {
			$prev = $`;
			$self = $g_and[$j];
			$next = $& . $';
			$next =~ s/^$g_and[$j]//;
			$part = "1";
		    }
		    next;
		} else {
		    $flag = 0;
		}
	    }
	}
    }
    ### or条件
    if($flag == 1 && @g_or > 0) {
	for($j=0;$j<@g_or&&$flag==1;$j++) {
	    if($g_or_i[$j] == 0) {
		## 全角１文字が全く含まれない場合
		if($title =~ /$g_or[$j]/) {
		    # キーワードがあった(続ける)
		    next;
		} elsif($contents =~ /$g_or[$j]/) {
		    # キーワードがあった(続ける)
		    if($in == 1 && $part eq "") {
			$prev = $`;
			$self = $&;
			$next = $';
			$part = "1";
		    }
		    next;
		} else {
		    # キーワードがなかった(やめる)
		    $flag = 0;
		}
	    } else {
		## 全角１文字が含まれる場合
		my $w;
		my $p = 0;
		my $f = 0;
		my @words = split(/\|/,$g_or[$j]);
		foreach $w ( @words ) {
		    $p = 1 if($w =~ /^$peuc$/);  # これは全角１文字だ
		    if($p == 1) {
			# 全角１文字
			if($title =~ /$w$feuc/) {
			    $f = 1;
			    last;
			}
			if($contents =~ /$w$feuc/) {
			    if($in == 1 && $part eq "") {
				$prev = $`;
				$self = $w;
				$next = $& . $';
				$next =~ s/^$w//;
				$part = "1";
			    }
			    $f = 1;
			    last;
			}
		    } else {
			# 全角１文字じゃない
			if($title =~ /$w/) {
			    $f = 1;
			    last;
			}
			if($contents =~ /$w/) {
			    if($in == 1 && $part eq "") {
				$prev = $`;
				$self = $&;
				$next = $';
				$part = "1";
			    }
			    $f = 1;
			    last;
			}
		    }
		}
		if($f == 1) {
		    # キーワードがあった
		    next;
		} else {
		    # キーワードがなかった
		    $flag = 0;
		    last;
		}
	    }
	}
    }
    ### not条件
    if($flag == 1 && @g_not > 0) {
	for($j=0;$j<@g_not&&$flag==1;$j++) {
	    if($g_not_i[$j] == 0) {
		## 全角１文字以外の場合
		if($contents =~ /$g_not[$j]/ || $title =~ /$g_not[$j]/) {
		    # キーワードがあった(やめる)
		    $flag = 0;
		} else {
		    # キーワードがなかった(続ける)
		    next;
		}
	    } else {
		## 全角１文字の場合
		if($contents =~ /$g_not[$j]$feuc/ ||
		   $title =~ /$g_not[$j]$feuc/) {
		    # キーワードがあった(やめる)
		    $flag = 0;
		} else {
		    # キーワードがなかった(続ける)
		    next;
		}
	    }
	}
    }
    ### title条件
    if($flag == 1 && @g_title > 0) {
	for($j=0;$j<@g_title&&$flag==1;$j++) {
	    if($g_title_i[$j] == 0) {
		## 全角１文字以外の場合
		if($title =~ /$g_title[$j]/) {
		    # キーワードがあった(続ける)
		    next;
		} else {
		    # キーワードがなかった(やめる)
		    $flag = 0;
		}
	    } else {
		## 全角１文字の場合
		if($title =~ /$g_title[$j]$feuc/) {
		    # キーワードがあった(続ける)
		    next;
		} else {
		    # キーワードがなかった(やめる)
		    $flag = 0;
		}
	    }
	}
    }
    ### url条件
    if($flag == 1 && @g_url > 0) {
	for($j=0;$j<@g_url&&$flag==1;$j++) {
	    if($url =~ /$g_url[$j]/) {
		# キーワードがあった(続ける)
		next;
	    } else {
		# キーワードがなかった(やめる)
		$flag = 0;
	    }
	}
    }

    ## 表示範囲のもののみmatch配列に保存する
    if($flag == 1 && $in == 1) {
	# タイトル中のマッチ文字列をハイライト化
	if($f_highlight == 1) {
            highlight(\$title,$hl_open,$hl_close,1);
	}

	# HTML中身の部分を抽出
	if($part eq "") {
	    ($part,undef) = &fold($contents,$f_extract_f + $f_extract_b);
	    $part .= ". . .";
	} else {
	    $part = extract(\$prev,\$self,\$next);
	}

	# 抽出部分のハイライト化
	if($f_highlight == 1) {
	    highlight(\$part,$hl_open,$hl_close,0);
	}

	# 配列に登録
	push(@match,"$url\t$title\t$part");
    }
    $v_total++ if($flag == 1);
}

### 処理時間のセット
getcputime();

###
### 検索結果の表示
###
printpage();

### ログの出力
if($f_log == 1) {
    outputlog();
}

### 終了
exit;

######################
### 引数関係の関数 ###
######################

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
	# 同じ属性が複数ある場合は，後の方が有効になる
	# query属性の場合は' 'で連結する
	if($attribute eq "query" && defined $qarg{$attribute}) {
	    $qarg{$attribute} .= " $value";
	} else {
	    $qarg{$attribute} = $value;
	}
    }
    return \%qarg;
}

###
### CGI引数のチェック
###
sub checkinvalid {
    if($v_rpp == 0 && $v_set != 1) {
	# 結果の全部表示なのに2番目以上のセットを要求した
	printerror("検索結果範囲外です");
    }
    if($v_set < 1 || $v_rpp < 0) {
	# セットが0以下または表示数が0より小さい呼び出し
	printerror("検索結果範囲外です");
    }
}

##########################
### クエリー関係の関数 ###
##########################

###
### クエリーの正規化
###
sub normalize {
    my $string = $_[0];		# クエリーへの参照(入力)

    &jcode::h2z_euc($string);	# 半角カナを全角に
    &jcode::tr($string,'　，（）',',,()');
    $$string =~ s/\s/,/g;	# 空白文字をデリミタに
    $$string =~ s/,+/,/g;	# ２個以上続くデリミタを削除
}

###
### 全角英数記号を半角英数記号に変換
###
sub z2h {
    my $string = $_[0];		# 変換する文字列への参照(入力)

    &jcode::tr($string,'０-９Ａ-Ｚａ-ｚ＋］［．（）？／＠',
	       '0-9A-Za-z+][.()?/@');
}

###
### クエリー中の正規表現のメタ文字のエスケープ
###
sub escapequery {
    my ($i, $j);

    # $g_??_i[$i]の意味は，
    # 1 = 全角1文字だけ
    # 0 = その他

    # AND条件
    for($i=0;$i<@g_and;$i++) {
	$g_and[$i] =~ s/($meta)/\\$1/g;
	if($g_and[$i] =~ /^$peuc$/) {
	    $g_and_i[$i] = 1;
	} else {
	    $g_and_i[$i] = 0;
	    $g_and[$i] =~ s/([a-zA-Z])/'[' . lc($1) . uc($1) . ']'/eg;
	}
    }

    # OR条件
    for($i=0;$i<@g_or;$i++) {
	$g_or[$i] =~ s/($meta)/\\$1/g;
	$g_or[$i] =~ s/,/\|/g;
	my @words = split(/\|/,$g_or[$i]);
	$g_or_i[$i] = 0;
	for($j=0;$j<@words;$j++) {
	    if($words[$j] =~ /^$peuc$/) {
		$g_or_i[$i] = 1;
	    }
	    $words[$j] =~ s/([a-zA-Z])/'[' . lc($1) . uc($1) . ']'/eg;
	}
	$g_or[$i] = join('|',@words);
    }

    # NOT条件
    for($i=0;$i<@g_not;$i++) {
	$g_not[$i] =~ s/($meta)/\\$1/g;
	if($g_not[$i] =~ /^$peuc$/) {
	    $g_not_i[$i] = 1;
	} else {
	    $g_not_i[$i] = 0;
	    $g_not[$i] =~ s/([a-zA-Z])/'[' . lc($1) . uc($1) . ']'/eg;
	}
    }

    # TITLE条件
    for($i=0;$i<@g_title;$i++) {
	$g_title[$i] =~ s/($meta)/\\$1/g;
	if($g_title[$i] =~ /^$peuc$/) {
	    $g_title_i[$i] = 1;
	} else {
	    $g_title_i[$i] = 0;
	    $g_title[$i] =~ s/([a-zA-Z])/'[' . lc($1) . uc($1) . ']'/eg;
	}
    }

    # URL条件
    for($i=0;$i<@g_url;$i++) {
	$g_url[$i] =~ s/($meta)/\\$1/g;
	$g_url[$i] =~ s/([a-zA-Z])/'[' . lc($1) . uc($1) . ']'/eg;
    }
}

###
### url条件を正規表現に使える様に変換
###
sub changeregexp {
    my $queries = $_[0];	# url条件配列への参照(入力)
    my $i;			# インクリメンタル用変数

    for($i=0;$i<@$queries;$i++) {
	# . -> \.
	$queries->[$i] =~ s/\./\\./g;
	# / -> \/
	$queries->[$i] =~ s/\//\\\//g;
    }
}

##############################
### インデックス関係の関数 ###
##############################

###
### インデックスの読み込み
###
sub readindex {
    my $value;			# インデックスの中身
    my $i;			# インクリメンタル値

    # ファイルのオープン
    open(FILE,"<$g_indexfile");

    # インデックスの読み込み
    $i = 0;
    while(<FILE>) {
	# 改行を削除
	chomp;
	# ファイル名以外の部分を取り出す
	(undef,$value) = split(/\t/,$_,2);
	# 配列に登録
	$g_index[$i] = $value;
	$i++;
    }

    # ファイルのクローズ
    close(FILE);
    return($i);
}

###
### インデックスの件数取得
###
sub getindexnum {
    my $i;

    # ファイルのオープン
    open(FILE,"<$g_indexfile");

    # インデックスの読み込み
    $i = 0;
    while(<FILE>) {
	$i++;
    }

    # ファイルのクローズ
    close(FILE);
    return($i);
}


##############################
### 検索結果抽出関係の関数 ###
##############################

###
### マッチ部分の抽出
###
sub extract {
    my $front = $_[0];        # 前方文字列への参照(入力)
    my $keyword = $_[1];      # キーワード文字列への参照(入力)
    my $back = $_[2];         # 後方文字列への参照(入力)
    my $str = "";
    my $rev;
    my $tmp;

    $rev = reverse($$front);
    ($tmp,undef) = &fold($rev,$f_extract_f);
    $str .= reverse($tmp) . $$keyword;

    ($tmp,undef) = &fold($$back,$f_extract_b);
    $str .= "$tmp. . . ";

    return($str);
}

###
### ハイライト化
###
sub highlight {
    my $str = $_[0];        # 対象文字列への参照
    my $hl_open = $_[1];
    my $hl_close = $_[2];
    my $istitle = $_[3];
    my @all = ();
    my $target;

    splice(@all,$#all+1,0,@g_and);
    splice(@all,$#all+1,0,@g_or);
    splice(@all,$#all+1,0,@g_title) if($istitle);
    $target = join("|",@all);
    return if($target eq "");
    $$str =~ s/\G((?:$han1|$hank|$zen2|$zen3)*?)($target)/$1$hl_open$2$hl_close/g;
}

##############################
### 設定ファイル関係の関数 ###
##############################

###
### 設定ファイルの読み込みと解釈
###
sub parseconfig {
    # ファイルのオープン
    unless(open(FM,"<$g_config")) {
	printerror("設定ファイルが開けません");
    }

    # 設定の読み込み
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/ || $line =~ /^\n$/);
	if($line =~ /^set/) {
	    pf_set($line);
	    next;
	}
	if($line =~ /^begin (page|result|previous|next|pset|cset|nset|help)/) {
	    my $type = $1;
	    pf_page($line) if($type eq "page");
	    pf_result($line) if($type eq "result");
	    pf_previous($line) if($type eq "previous");
	    pf_next($line) if($type eq "next");
	    pf_pset($line) if($type eq "pset");
	    pf_cset($line) if($type eq "cset");
	    pf_nset($line) if($type eq "nset");
	    pf_help($line) if($type eq "help");
	}
    }

    close(FM);
    if(@f_page <= 0) {
	printerror("フォーマットの書式エラー(no page definition)");
    }
    if($f_result eq "") {
	printerror("フォーマットの書式エラー(no result definition)");
    }
    if($f_previous eq "" && existformat("previous")) {
	printerror("フォーマットの書式エラー(no previous definition)");
    }
    if($f_next eq "" && existformat("next")) {
	printerror("フォーマットの書式エラー(no next definition)");
    }
    if($f_pset eq "" && existformat("pset")) {
	printerror("フォーマットの書式エラー(no pset definition)");
    }
    if($f_cset eq "" && existformat("cset")) {
	printerror("フォーマットの書式エラー(no cset definition)");
    }
    if($f_nset eq "" && existformat("nset")) {
	printerror("フォーマットの書式エラー(no nset definition)");
    }
    if($f_help eq "") {
	printerror("フォーマットの書式エラー(no help definition)");
    }
}

###
### 下位フォーマットの存在チェック
###
sub existformat {
    my $format = $_[0];
    my $f;

    foreach $f ( @f_page ) {
	if($f eq $format) {
	    return(1);
	}
    }
    return(0);
}

###
### 変数解釈
###
sub pf_set {
    my $line = $_[0];

    if($line =~
       /\$(home|highlight|highlight_deco|tzdiff|notitle|log|logfile|logencoding|logformat|dateformat|encoding|extract_f|extract_b)=(.*)\n/) {
	my $var = $1;
	my $val = $2;

	if($var eq "home") {
	    $f_home = $val;
	} elsif($var eq "highlight") {
	    $f_highlight = $val;
	} elsif($var eq "highlight_deco") {
	    $f_highlight_deco = $val;
	} elsif($var eq "tzdiff") {
	    $f_tzdiff = $val;
	} elsif($var eq "notitle") {
	    $f_notitle = $val;
	} elsif($var eq "log") {
	    $f_log = $val;
	} elsif($var eq "logfile") {
	    $f_logfile = $val;
	} elsif($var eq "logencoding") {
	    $f_logencoding = $val;
	} elsif($var eq "logformat") {
	    $f_logformat = $val;
	} elsif($var eq "dateformat") {
	    $f_dateformat = $val;
	} elsif($var eq "encoding") {
	    $f_encoding = $val;
	} elsif($var eq "extract_f") {
	    $f_extract_f = $val;
	} elsif($var eq "extract_b") {
	    $f_extract_b = $val;
	}
    }
}

###
### pageフォーマット解釈
###
sub pf_page {
    my $str = "";

    # まず２重登録かどうかをチェックする
    if(@f_page > 0) {
	printerror("フォーマットの書式エラー(page redefinition)");
    }

    # とりあえずendまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$str .= $line;
    }

    # 下位フォーマットを見つける
    while($str) {
	if($str =~ /\$\$(result|previous|next|pset|cset|nset)\$\$/) {
	    my $p = $`;
	    my $c = $1;
	    my $n = $';
	    # 変数が含まれているかのチェック
	    if($p =~ /\$\$[a-z]*\$\$/) {
		push(@f_pageindex,"V");
		push(@f_page,$p);
	    } else {
		if($p !~ /^\n*$/) {
		    push(@f_pageindex,"N");
		    push(@f_page,$p);
		}
	    }

	    # 下位フォーマット
	    push(@f_pageindex,"F");
	    push(@f_page,"$c");

	    $str = $n;
	} else {
	    # 変数が含まれているかのチェック
	    if($str =~ /\$\$[a-z]*\$\$/) {
		push(@f_pageindex,"V");
		push(@f_page,$str);
	    } else {
		if($str !~ /^\n*$/) {
		    push(@f_pageindex,"N");
		    push(@f_page,$str);
		}
	    }

	    $str = "";
	}
    }
}

###
### resultフォーマット解釈
###
sub pf_result {
    my $line = $_[0];

    # まず２重登録かどうかをチェックする
    if($f_result != "") {
	printerror("フォーマットの書式エラー(result redefinition)");
    }

    # 表示件数を取得
    $line =~ /^begin result ([0-9]*)/;
    $f_result_num = $1;

    # endまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$f_result .= $line;
    }
}

###
### previousフォーマット解釈
###
sub pf_previous {
    # まず２重登録かどうかをチェックする
    if($f_previous != "") {
	printerror("フォーマットの書式エラー(previous redefinition)");
    }

    # endまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$f_previous .= $line;
    }
}

###
### nextフォーマット解釈
###
sub pf_next {
    # まず２重登録かどうかをチェックする
    if($f_next != "") {
	printerror("フォーマットの書式エラー(next redefinition)");
    }

    # endまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$f_next .= $line;
    }
}

###
### psetフォーマット解釈
###
sub pf_pset {
    my $line = $_[0];

    # まず２重登録かどうかをチェックする
    if($f_pset != "") {
	printerror("フォーマットの書式エラー(pset redefinition)");
    }

    # 表示件数を取得
    $line =~ /^begin pset ([0-9]*)/;
    $f_pset_num = $1;

    # endまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$f_pset .= $line;
    }
}

###
### csetフォーマット解釈
###
sub pf_cset {
    # まず２重登録かどうかをチェックする
    if($f_cset != "") {
	printerror("フォーマットの書式エラー(cset redefinition)");
    }

    # endまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$f_cset .= $line;
    }
}

###
### nsetフォーマット解釈
###
sub pf_nset {
    my $line = $_[0];

    # まず２重登録かどうかをチェックする
    if($f_nset != "") {
	printerror("フォーマットの書式エラー(nset redefinition)");
    }

    # 表示件数を取得
    $line =~ /^begin nset ([0-9]*)/;
    $f_nset_num = $1;

    # endまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$f_nset .= $line;
    }
}

###
### helpフォーマット解釈
###
sub pf_help {
    # まず２重登録かどうかをチェックする
    if($f_help != "") {
	printerror("フォーマットの書式エラー(help redefinition)");
    }

    # endまで読み込む
    while(<FM>) {
	my $line = $_;
	next if($line =~ /^\#/);
	last if($line =~ /^end/);
	$f_help .= $line;
    }

    if($f_help =~ /\$\$indexnum\$\$/) {
	$f_exist_indexnum = 1;
    } else {
	$f_exist_indexnum = 0;
    }
}

##################################
### フォーマット変数関係の関数 ###
##################################

###
### CPU時間の測定
###
sub getcputime {
    my $cpu_finish = (times)[0];
    $v_cputime = $cpu_finish - $v_cputime;
}

###
### インデックスの最終更新日時の取得
###
sub getindexdate {
    my ($s, $m, $h, $d, $mon, $year);

    ($s,$m,$h,$d,$mon,$year) =
	localtime((stat($g_indexfile))[9] + $f_tzdiff * 3600);

    return(formatdate($f_dateformat,$year,$mon,$d,$h,$m,$s));
}

###
### 現在日時の取得
###
sub getnowdate {
    my ($s, $m, $h, $d, $mon, $year);

    ($s,$m,$h,$d,$mon,$year) = localtime(time + $f_tzdiff * 3600);

    return(formatdate($f_dateformat,$year,$mon,$d,$h,$m,$s));
}

###
### 日時表示フォーマット
###
sub formatdate {
    my $f = $_[0];
    my $year = $_[1];
    my $month = $_[2];
    my $day = $_[3];
    my $hour = $_[4];
    my $minute = $_[5];
    my $second = $_[6];

    $year += 1900;
    $month += 1;
    $second = "0$second" if($second < 10);
    $minute = "0$minute" if($minute < 10);
    $hour = "0$hour" if($hour < 10);
    $day = "0$day" if($day < 10);
    $month = "0$month" if($month < 10);

    $f =~ s/year/$year/g;
    $f =~ s/month/$month/g;
    $f =~ s/day/$day/g;
    $f =~ s/hour/$hour/g;
    $f =~ s/minute/$minute/g;
    $f =~ s/second/$second/g;

    return($f);
}


######################
### 出力関係の関数 ###
######################

###
### HTML Content-type出力
###
sub printcontenttype {
	print "Content-type: text/html\n\n";
}

###
### エラー用出力
###
sub printerror {
    my $message = $_[0];	# エラーメッセージ(入力)

    if($f_encoding eq "shift_jis") {
	&jcode::convert(\$message,"sjis");
    } elsif($f_encoding eq "iso-2022-jp") {
	&jcode::convert(\$message,"jis");
    }
    print "<p><h2><font color=red>$message</font></h2>\n";
    print "</body></html>";
    exit;
}

###
### 検索結果ページの出力
###
sub printpage {
    my ($i, $q);

    # 表示件数
    $v_displaynum = $#match + 1;

    # 表示の先頭項目番号と後尾項目番号
    if($v_total == 0) {
	$v_from = 0;
    } else {
	$v_from = $d_start + 1;
    }
    $v_to = $d_start + $v_displaynum;

    # クエリーのエンコーディング
    $q = $v_query;
    $q =~ s/([^\w ])/'%' . unpack('H2',$1)/eg;
    $q =~ tr/ /+/;

    # cgi呼び出しで共通な部分
    $cgicall = "$v_msearch?";
    $cgicall .= "index=$v_index&" if($v_index);
    $cgicall .= "config=$v_config&" if($v_config);
    $cgicall .= "query=$q&num=$v_rpp";

    # 総セット数の計算
    if($v_rpp != 0) {
	$tset = int($v_total / $v_rpp) + 1;
	$tset-- if(($v_total % $v_rpp) == 0);
    } else {
	$tset = 1;
    }
    if($v_total == 0) {
	$tset = -1;
    }

    # クエリーのサニタイジング
    $v_query =~ s/&/&amp;/g;
    $v_query =~ s/</&lt;/g;
    $v_query =~ s/>/&gt;/g;
    $v_query =~ s/"/&quot;/g;
    $v_query =~ s/'/&#39;/g;

    for($i=0;$i<@f_page;$i++) {
	if($f_pageindex[$i] eq "N") {
	    # フォーマット変数がない部分
	    if($f_encoding eq "shift_jis") {
		&jcode::convert(\$f_page[$i],"sjis");
	    } elsif($f_encoding eq "iso-2022-jp") {
		&jcode::convert(\$f_page[$i],"jis");
	    }
	    print $f_page[$i];
	} elsif($f_pageindex[$i] eq "V") {
	    # フォーマット変数がある部分
	    $f_page[$i] =~ s/\$\$encoding\$\$/$f_encoding/g;
	    $f_page[$i] =~ s/\$\$msearch\$\$/$v_msearch/g;
	    $f_page[$i] =~ s/\$\$home\$\$/$v_home/g;
	    $f_page[$i] =~ s/\$\$query\$\$/$v_query/g;
	    $f_page[$i] =~ s/\$\$index\$\$/$v_index/g;
	    $f_page[$i] =~ s/\$\$config\$\$/$v_config/g;
	    $f_page[$i] =~ s/\$\$rpp\$\$/$v_rpp/g;
	    $f_page[$i] =~ s/\$\$total\$\$/$v_total/g;
	    $f_page[$i] =~ s/\$\$set\$\$/$v_set/g;
	    $f_page[$i] =~ s/\$\$from\$\$/$v_from/g;
	    $f_page[$i] =~ s/\$\$to\$\$/$v_to/g;
	    $f_page[$i] =~ s/\$\$displaynum\$\$/$v_displaynum/g;
	    $f_page[$i] =~ s/\$\$cputime\$\$/$v_cputime/g;
	    $f_page[$i] =~ s/\$\$indexdate\$\$/$v_indexdate/g;
	    $f_page[$i] =~ s/\$\$indexnum\$\$/$v_indexnum/g;
	    $f_page[$i] =~ s/\$\$nowdate\$\$/$v_nowdate/g;
	    $f_page[$i] =~ s/\$\$msearchhp\$\$/$v_msearchhp/g;
	    $f_page[$i] =~ s/\$\$version\$\$/$v_version/g;
	    if($f_encoding eq "shift_jis") {
		&jcode::convert(\$f_page[$i],"sjis");
	    } elsif($f_encoding eq "iso-2022-jp") {
		&jcode::convert(\$f_page[$i],"jis");
	    }
	    print $f_page[$i];
	} elsif($f_pageindex[$i] eq "F") {
	    # 下位フォーマットの場合
	    if($f_page[$i] eq "result") {
		# resultフォーマットの場合
		printresult();
	    } elsif($f_page[$i] eq "previous") {
		# previousフォーマットの場合
		printprevious();
	    } elsif($f_page[$i] eq "next") {
		# nextフォーマットの場合
		printnext();
	    } elsif($f_page[$i] eq "pset") {
		# psetフォーマットの場合
		printpset();
	    } elsif($f_page[$i] eq "cset") {
		# csetフォーマットの場合
		printcset();
	    } elsif($f_page[$i] eq "nset") {
		# nsetフォーマットの場合
		printnset();
	    }
	}
    }
}

###
### ヘルプページの出力
###
sub printhelp {
    $f_help =~ s/\$\$encoding\$\$/$f_encoding/g;
    $f_help =~ s/\$\$msearch\$\$/$v_msearch/g;
    $f_help =~ s/\$\$home\$\$/$v_home/g;
    $f_help =~ s/\$\$index\$\$/$v_index/g;
    $f_help =~ s/\$\$config\$\$/$v_config/g;
    $f_help =~ s/\$\$rpp\$\$/$v_rpp/g;
    $f_help =~ s/\$\$cputime\$\$/$v_cputime/g;
    $f_help =~ s/\$\$indexdate\$\$/$v_indexdate/g;
    $f_help =~ s/\$\$indexnum\$\$/$v_indexnum/g;
    $f_help =~ s/\$\$nowdate\$\$/$v_nowdate/g;
    $f_help =~ s/\$\$msearchhp\$\$/$v_msearchhp/g;
    $f_help =~ s/\$\$version\$\$/$v_version/g;

    if($f_encoding eq "shift_jis") {
	&jcode::convert(\$f_help,"sjis");
    } elsif($f_encoding eq "iso-2022-jp") {
	&jcode::convert(\$f_help,"jis");
    }
    print $f_help;
}

###
### resultフォーマットの出力
###
sub printresult {
    my ($i, $orgurl, $format);
    my ($resultnum, $url, $title, $summary);
    my $reghl = "";           # URLハイライト化の正規表現

    # URLハイライト用の正規表現作成
    $reghl = join("|",@g_url) if(@g_url);

    for($i=0;$i<@match;$i++) {
	# フォーマットの初期化
	$format = $f_result;

	# 1項目取り出し
	($orgurl,$title,$summary) = split(/\t/,$match[$i]);

	# 残りのフォーマット変数のバインド
	$resultnum = $v_from + $i;
	$url = $orgurl;
	if($reghl ne "") {
	    $url =~ s/($reghl)/$hl_open\1$hl_close/g;
	}
	$title = $f_notitle if($title eq "");

	# フォーマット変数の置換
	$format =~ s/\$\$resultnum\$\$/$resultnum/g;
	$format =~ s/\$\$url\$\$/$orgurl/g;
	$format =~ s/\$\$urldeco\$\$/$url/g;
	$format =~ s/\$\$title\$\$/$title/g;
	$format =~ s/\$\$summary\$\$/$summary/g;
	$format =~ s/\$\$rpp\$\$/$v_rpp/g;

	if($f_encoding eq "shift_jis") {
	    &jcode::convert(\$format,"sjis");
	} elsif($f_encoding eq "iso-2022-jp") {
	    &jcode::convert(\$format,"jis");
	}
	print $format;
    }
}

###
### previousフォーマットの出力
###
sub printprevious {
    my ($p, $previousurl, $format);

    # 現セットが1の場合は出力しない
    return if($v_set == 1);

    # 全件表示の場合は出力しない
    return if($v_rpp == 0);

    # 検索結果が0件の場合は出力しない
    return if($tset == -1);

    # フォーマット変数のバインド
    $p = $v_set - 1;
    $previousurl = "$cgicall&set=$p";

    # フォーマット変数の置換
    $format = $f_previous;
    $format =~ s/\$\$previousurl\$\$/$previousurl/g;
    $format =~ s/\$\$rpp\$\$/$v_rpp/g;

    if($f_encoding eq "shift_jis") {
	&jcode::convert(\$format,"sjis");
    } elsif($f_encoding eq "iso-2022-jp") {
	&jcode::convert(\$format,"jis");
    }
    print $format;
}

###
### nextフォーマットの出力
###
sub printnext {
    my ($n, $nexturl, $format);

    # 現セットが最終セットの場合は出力しない
    return if($v_set == $tset);

    # 全件表示の場合は出力しない
    return if($v_rpp == 0);

    # 検索結果が0件の場合は出力しない
    return if($tset == -1);

    # フォーマット変数のバインド
    $n = $v_set + 1;
    $nexturl = "$cgicall&set=$n";

    # フォーマット変数の置換
    $format = $f_next;
    $format =~ s/\$\$nexturl\$\$/$nexturl/g;
    $format =~ s/\$\$rpp\$\$/$v_rpp/g;

    if($f_encoding eq "shift_jis") {
	&jcode::convert(\$format,"sjis");
    } elsif($f_encoding eq "iso-2022-jp") {
	&jcode::convert(\$format,"jis");
    }
    print $format;
}

###
### psetフォーマットの出力
###
sub printpset {
    my ($i, $setnum, $seturl, $format);

    for($i=0;$i<$f_pset_num;$i++) {
	$setnum = $v_set - $f_pset_num + $i;
	next if($setnum < 1);  # 第１セット以前は無視
	$seturl = "$cgicall&set=$setnum";

	# フォーマット変数の置換
	$format = $f_pset;
	$format =~ s/\$\$seturl\$\$/$seturl/g;
	$format =~ s/\$\$setnum\$\$/$setnum/g;
	$format =~ s/\$\$rpp\$\$/$v_rpp/g;

	if($f_encoding eq "shift_jis") {
	    &jcode::convert(\$format,"sjis");
	} elsif($f_encoding eq "iso-2022-jp") {
	    &jcode::convert(\$format,"jis");
	}
	print $format;
    }
}

###
### csetフォーマットの出力
###
sub printcset {
    my $format;

    # 検索結果が0件か結果セットが1ページの場合は出力しない
    return if($tset == -1 || $tset == 1);

    # 全件表示の場合は出力しない
    return if($v_rpp == 0);

    # フォーマット変数の置換
    $format = $f_cset;
    $format =~ s/\$\$set\$\$/$v_set/g;
    $format =~ s/\$\$rpp\$\$/$v_rpp/g;

    if($f_encoding eq "shift_jis") {
	&jcode::convert(\$format,"sjis");
    } elsif($f_encoding eq "iso-2022-jp") {
	&jcode::convert(\$format,"jis");
    }
    print $format;
}

###
### nsetフォーマットの出力
###
sub printnset {
    my ($i, $setnum, $seturl, $format);

    for($i=0;$i<$f_nset_num;$i++) {
	$setnum = $v_set + $i + 1;
	last if($setnum > $tset);  # 最終セット以降は無視
	$seturl = "$cgicall&set=$setnum";

	# フォーマット変数の置換
	$format = $f_nset;
	$format =~ s/\$\$seturl\$\$/$seturl/g;
	$format =~ s/\$\$setnum\$\$/$setnum/g;
	$format =~ s/\$\$rpp\$\$/$v_rpp/g;

	if($f_encoding eq "shift_jis") {
	    &jcode::convert(\$format,"sjis");
	} elsif($f_encoding eq "iso-2022-jp") {
	    &jcode::convert(\$format,"jis");
	}
	print $format;
    }
}

###
### ログの出力
###
sub outputlog {
    my $ua = $ENV{'HTTP_USER_AGENT'};
    my ($str, $remote);

    $remote = gethostname($ENV{'REMOTE_ADDR'}) if($f_logformat =~ /remote/);

    # ロック開始
    if(mylock() != 1) {
	printerror("ロックに失敗しました");
    }

    # ログファイルのオープン
    open(LF,">>$f_logfile") or printerror("ログファイルが開けません");

    # ログの書き出し
    $str = $f_logformat;
    $str =~ s/date/$v_nowdate/g;
    $str =~ s/remote/$remote/g;
    $str =~ s/ua/$ua/g;
    $str =~ s/hit/$v_total/g;
    $str =~ s/query/$v_query/g;
    $str =~ s/\\n/\n/g;
    $str =~ s/\\t/\t/g;
    if($f_logencoding eq "shift_jis") {
	&jcode::convert(\$str,"sjis");
    } elsif($f_logencoding eq "iso-2022-jp") {
	&jcode::convert(\$str,"jis");
    }
    print LF "$str";

    # ログファイルのクローズ
    close(LF);

    myunlock();
}

###
### ホスト名の逆引き
###
sub gethostname {
    my $ip = $_[0];            # REMOTE_ADDRの値
    my $packedaddr = pack("C4",split(/\./,$ip));
    my $host;

    ($host,undef,undef,undef,undef) = gethostbyaddr($packedaddr,2);

    if($host ne "") {
	return("$host($ip)");
    } else {
	return($ip);
    }
}

###
### シグナルハンドラー
###
sub sighandler {
    my $sig = $_[0];            # シグナルの種類(入力)

    if(-d $g_lock) {
        rmdir($g_lock);
    }
    exit;
}

###
### ロックする(flockがなくてもOK)
###
sub mylock {
    my ($alivetime, $i);

    # ロック解除が失敗している場合に備えて
    $alivetime = (stat($g_lock))[9] - time();
    if($alivetime > 60) {
        rmdir($g_lock);
    }

    # 3回(3秒)までロック取得のリトライする
    for($i=0;$i<3;$i++) {
        if(mkdir($g_lock,0777)) {
            # シグナルハンドラーを登録
            $SIG{'TERM'} = \&sighandler;
            $SIG{'INT'} = \&sighandler;
            $SIG{'PIPE'} = \&sighandler;
            $SIG{'HUP'} = \&sighandler;
            $SIG{'QUIT'} = \&sighandler;
            return(1);
        } else {
            sleep(1);           # 待つ
        }
    }

    return(0);
}

###
### アンロック
###
sub myunlock {
    if(-d $g_lock) {
        rmdir($g_lock);
    }
}
