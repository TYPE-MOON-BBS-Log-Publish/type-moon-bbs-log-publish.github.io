#=============================================================================#
#                  indexing.pl - インデックス作成モジュール                   #
#        Copyright (C) 2000-2003, Katsushi Matsuda. All Right Reserved.       #
#=============================================================================#

####################
### 各種変数定義 ###
####################

$g_index = "";			# いわゆるインデックスファイル
%g_index = ();			# インデックスのハッシュ
				# key = ファイル名
				# val = URL,最終更新時刻,タイトル,HTMLの中身
$g_include_dir = "";		# インデックス対象ディレクトリ
$g_include_url = "";		# インデックス対象ディレクトリのURL
@g_suffix = ();			# インデックス対象ファイルの拡張子
@g_exclude_dir = ();		# 非インデックス対象ディレクトリ
@g_exclude_reg_dir = ();	# 非インデックス対象ディレクトリ(正規表現)
@g_exclude_file = ();		# 非インデックス対象ファイル
@g_exclude_reg_file = ();	# 非インデックス対象ファイル(正規表現)
$g_exclude_keys = "";		# 非インデックス対象キーワード
$g_sort = "";


###
### インデックス作成の主関数
###
sub makeindex {
    my $files;			# インデックス対象ファイルハッシュへの参照
    my $io;			# バッファリング用ファイルハンドル
    my $i;			# インクリメンタル変数(使いまわし)
    my $file;			# ファイル名
    my @del_files = ();		# 削除する対象ファイル
    my @add_files = ();		# 追加する対象ファイル
    my @mod_files = ();		# 更新する対象ファイル
    my $n_del = 0;		# インデックスから削除した対象ファイルの数
    my $n_add = 0;		# インデックスに追加した対象ファイルの数
    my $n_mod = 0;		# インデックスに更新した対象ファイルの数
    my $t_pass = "";		# パスワード

    ### インデックス名を作成
    if($qarg->{'index'} ne "") {
	$g_index = "./" . $qarg->{'index'} . ".idx";
    } else {
	$g_index = "./default.idx";
    }

    ### 引数の値を変数代入
    # インデックス対象ディレクトリ
    if($qarg->{'includedir'} ne "") {
	$g_include_dir = $qarg->{'includedir'};
	# 最後は"/"で終わる様に
	$g_include_dir .= "/" if($g_include_dir !~ /\/$/);
    }
    # インデックス対象ファイルのURL
    if($qarg->{'includeurl'} ne "") {
	$g_include_url = $qarg->{'includeurl'};
	# 最初は"http"で始まる様に
	$g_include_url = "http://" .
	    $g_include_url if($g_include_url !~ /^http/);
	# 最後は"/"で終わる様に
	$g_include_url .= "/" if($g_include_url !~ /\/$/);
    }
    # インデックス対象ファイルの拡張子
    if($qarg->{'suffix'} ne "") {
	@g_suffix = split(/,/,$qarg->{'suffix'});
    } else {
	@g_suffix = split(/,/,".html,.htm");
    }
    # 非インデックス対象ディレクトリ
    if($qarg->{'excludedir'} ne "") {
	my @tarray = ();
	my $tmp;
	@tarray = split(/,/,$qarg->{'excludedir'});
	foreach $tmp ( @tarray ) {
	    if($tmp =~ /\((.*)\)/) {
		# 正規表現形の場合
		push(@g_exclude_reg_dir,$1);
	    } else {
		# 非正規表現形の場合
		$tmp = $g_include_dir . $tmp;
		$tmp .= "/" if($tmp !~ /\/$/);
		push(@g_exclude_dir,$tmp);
	    }
	}
    }
    # 非インデックス対象ファイル
    if($qarg->{'excludefile'} ne "") {
	my @tarray = ();
	my $tmp;
	@tarray = split(/,/,$qarg->{'excludefile'});
	foreach $tmp ( @tarray ) {
	    if($tmp =~ /\((.*)\)/) {
		# 正規表現形の場合
		push(@g_exclude_reg_file,$1);
	    } else {
		# 非正規表現形の場合
		$tmp = $g_include_dir . $tmp;
		push(@g_exclude_file,$tmp);
	    }
	}
    }
    # 非インデックス対象キーワード
    if($qarg->{'excludekey'} ne "") {
	$g_exclude_keys = $qarg->{'excludekey'};
	&jcode::h2z_euc(\$g_exclude_keys);
	&jcode::tr(\$g_exclude_keys,'０-９Ａ-Ｚａ-ｚ＋］［．（）？／＠−',
		   '0-9A-Za-z+][.()?/@-');
	$g_exclude_keys =~ s/,/\|/g;
    }
    # ランキング方法
    if($qarg->{'sort'} ne "") {
	$g_sort = $qarg->{'sort'};
    } else {
	$g_sort = "NONE";
    }

    printout("インデックス作成を開始します\n");
    # 既存のインデックスがあれば読み込む(indexは%g_indexに入る)
    printout("■■■既存のインデックスを読み込みます\n");
    $i = readindex($g_index,\%g_index) if(-f $g_index);
    if(-f $g_index) {
	printout("■■■完了($iファイル)\n");
    } else {
	printout("■■■完了(0ファイル)\n");
    }

    # インデックス対象ファイルの収集
    printout("■■■インデックス化するファイルを収集しています\n");
    $files = collectfiles($g_include_dir,\@g_suffix,\@g_exclude_dir,
			  \@g_exclude_reg_dir,\@g_exclude_file,
			  \@g_exclude_reg_file);

    $i = keys(%$files);
    printout("■■■完了($iファイル)\n");

    # 削除ファイルと更新ファイルの収集
    printout("■■既存インデックスとの比較\n") if($debug);
    foreach $file (keys %g_index) {
	if($files->{$file} eq "") {
	    # インデックスにあり，対象ファイルにない場合
	    $n_del++;		# 削除数をインクリメント
	    push(@del_files,$file);
	} else {
	    # インデックスにも対象ファイルにもある場合
	    my $mtime;		# インデックスの値中の最終更新時刻
	    $mtime = (split(/\t/,$g_index{$file}))[1];
	    printout("■$file:前=$files->{$file}, 今回=$mtime\n") if($debug);
	    if($files->{$file} > $mtime) {
		# 更新日が新しい場合
		$n_mod++;	# 更新数をインクリメント
		push(@mod_files,$file);
	    }
	}
    }
    printout("■■完了($n_modファイル)\n") if($debug);

    # 削除ファイルの処理
    printout("■■インデックスから削除するファイル\n") if($debug);
    while(@del_files) {
	my $file = shift(@del_files);
	printout("■削除ファイル:$file\n") if($debug);
	delete $g_index{$file}; # インデックスから削除
    }
    printout("■■完了\n") if($debug);
    printout("■■■インデックスから削除($n_delファイル)\n");

    # 更新ファイルの処理
    printout("■■インデックスで更新するファイル\n") if($debug);
    while(@mod_files) {
	my ($i_url,$i_mtime,$i_title,$i_contents);
	my $file = shift(@mod_files);
	delete $g_index{$file};	# インデックスから削除
	# インデックス作成
	($i_url,$i_mtime,$i_title,$i_contents) =
	    makedata($file,$g_include_dir,$g_include_url,$g_exclude_keys);
	# インデックスに追加
#	$g_index{$file} = join('\t',$i_url,$i_mtime,$i_title,$i_contents);
	$g_index{$file} = "$i_url\t$i_mtime\t$i_title\t$i_contents";
	printout("■更新ファイル:$file\n") if($debug);
    }
    printout("■■完了($n_modファイル)\n") if($debug);
    printout("■■■インデックスの更新($n_modファイル)\n");
	
    # 新規ファイルの処理
    printout("■■インデックスに追加するファイル\n") if($debug);
    foreach $file (keys %$files) {
	if($g_index{$file} eq "") {
	    # 対象ファイルにあり，インデックスにない場合
	    my ($i_url,$i_mtime,$i_title,$i_contents);
	    $n_add++;		# 追加数をインクリメント
	    # インデックス作成
	    ($i_url,$i_mtime,$i_title,$i_contents) =
		makedata($file,$g_include_dir,$g_include_url,$g_exclude_keys);
	    # インデックスに追加
#	    $g_index{$file} = join('\t',$i_url,$i_mtime,$i_title,$i_contents);
	    $g_index{$file} = "$i_url\t$i_mtime\t$i_title\t$i_contents";
	    printout("■追加ファイル:$file\n") if($debug);
	}
    }
    printout("■■■インデックスに追加($n_addファイル)\n");

    # インデックスを書き出す
    if($n_del > 0 || $n_mod > 0 || $n_add > 0) {
	printout("■■■インデックスを保存しています\n");
	$i = writeindex($g_index,\%g_index);
	printout("■■■完了($iファイル)\n");
    } else {
	printout("■■■インデックスは最新です\n");
    }
    printout("インデックス作成は完了しました\n");
}


###
### インデックスの読み込み
###
sub readindex {
    my $fn = $_[0];		# インデックスのファイル名(引数)
    my $index = $_[1];		# インデックスへの参照(引数)
    my $key;			# ハッシュのキー
    my $value;			# ハッシュの値
    my $i;			# インクリメンタル値

    # ファイルのオープン
    open(FILE,"<$fn");

    printout("■■インデックスの読み込み\n") if($debug);

    # インデックスの読み込み
    $i = 0;
    while(<FILE>) {
	# 改行を削除
	chomp;
	# キーと値に分解
	($key,$value) = split(/\t/,$_,2);
	# ハッシュに登録
	$index->{$key} = $value;
	$i++;
	printout("■Read:$key\n") if($debug);
    }

    # ファイルのクローズ
    close(FILE);
    printout("■■完了($iファイル)\n") if($debug);
    return($i);
}

###
### インデックスの書き込み
###
sub writeindex {
    my $fn = $_[0];		# インデックスのファイル名(引数)
    my $index = $_[1];		# インデックスへの参照(引数)
    my $key;			# ハッシュのキー
    my $value;			# ハッシュの値
    my $i;			# インクリメンタル値
    my @unsort = ();
    my @sorted;

    # ファイルのオープン(破壊的)
    if(!open(FILE,">$fn")) {
	printout("ファイルオープンエラー\n");
    }

    # 各インデックスの書き込み
    printout("■■インデックスの書き込み\n") if($debug);

    # まずハッシュを配列化
    while(($key,$value) = each(%$index)) {
	push(@unsort,"$key\t$value");
    }
    printout("■配列化完了\n") if($debug);

    # ソート
    if($g_sort eq "MODIFY-DESC") {
	@sorted = sort sort_modify_desc @unsort;
    } elsif($g_sort eq "MODIFY-ASC") {
	@sorted = sort sort_modify_asc @unsort;
    } elsif($g_sort eq "TITLE-DESC") {
	@sorted = sort sort_title_desc @unsort;
    } elsif($g_sort eq "TITLE-ASC") {
	@sorted = sort sort_title_asc @unsort;
    } elsif($g_sort eq "URL-DESC") {
	@sorted = sort sort_url_desc @unsort;
    } elsif($g_sort eq "URL-ASC") {
	@sorted = sort sort_url_asc @unsort;
    } else {
	@sorted = @unsort;
    }
    printout("■ソート完了\n") if($debug);

    printout("■書き出し ") if($debug);
    for($i=0;$i<$#sorted+1;$i++) {
	printout("*") if($debug);
	print FILE "$sorted[$i]\n";
    }
    printout("\n") if($debug);

    # ファイルのクローズ
    close(FILE);
    printout("■■完了($iファイル)\n") if($debug);

    return($i);
}

###
### インデックス対象ファイルの収集
###
sub collectfiles {
    my $dir = $_[0];		# インデックス対象ディレクトリ(引数)
    my $suffix = $_[1];		# 対象ファイルの拡張子への参照(引数)
    my $ex_dir = $_[2];		# 非対象ディレクトリへの参照(引数)
    my $ex_reg_dir = $_[3];	# 非対象ディレクトリ(正)への参照(引数)
    my $ex_file = $_[4];	# 非対象ファイルへの参照(引数)
    my $ex_reg_file = $_[5];	# 非対象ファイル(正)への参照(引数)
    local %files = ();		# 対象ファイルのハッシュ(戻り値)
				# key = ファイル名
				# val = 最終更新時刻

    ## インデックス対象ファイルの収集
    printout("■■対象ファイルの調査\n") if($debug);
    reccollect($dir,$suffix,$ex_dir,$ex_reg_dir,$ex_file,$ex_reg_file);

    # 収集した対象ファイルのハッシュを返す
    printout("■■完了\n") if($debug);
    return(\%files);
}

###
### インデックス対象ファイルの収集(再帰用)
###
sub reccollect {
    my $curdir = $_[0];		# カレントディレクトリ(引数)
    my $suffix = $_[1];		# 対象ファイルの拡張子への参照(引数)
    my $ex_dir = $_[2];		# 非対象ディレクトリへの参照(引数)
    my $ex_reg_dir = $_[3];	# 非対象ディレクトリ(正)への参照(引数)
    my $ex_file = $_[4];	# 非対象ファイルへの参照(引数)
    my $ex_reg_file = $_[5];	# 非対象ファイル(正)への参照(引数)
    my @dirs = ();		# カレントディレクトリに含まれるディレクトリ
    my $file;			# 逐次調査するファイル名

    # ディレクトリのオープン
    opendir(DIR,$curdir) or return;
    ## ディレクトリエントリを調査
    while($file = readdir(DIR)) {
	my $fpath;

	# カレントと親ディレクトリは無視
	if($file eq "." || $file eq "..") {
	    next;
	}
	# ディレクトリ込みのファイル名に変換
	$fpath = $curdir . $file;
	# ディレクトリかどうかのチェック
	if(isdirectory($fpath) == 1) {
	    # ファイルはディレクトリ
	    if(isexcluderegdir($file,$ex_reg_dir) == 1) {
		# このディレクトリは非対象ディレクトリ
		printout("■非対象ディレクトリ:$fpath\n") if($debug);
		next;
	    }
	    $fpath .= "/";	# ディレクトリの最後に"/"を付ける
	    if(isexcludedir($fpath,$ex_dir) == 1) {
		# このディレクトリは非対象ディレクトリ
		printout("■非対象ディレクトリ:$fpath\n") if($debug);
		next;
	    } else {
		# このディレクトリは再帰させるためにスタックに保存
		push(@dirs,$fpath);
	    }
	} else {
	    # ファイルはディレクトリではない
	    if(isexcluderegfile($file,$ex_reg_file) == 1) {
		# このファイルは非対象ファイル
		printout("■非対象ファイル:$fpath\n") if($debug);
		next;
	    } elsif(isexcludefile($fpath,$ex_file) == 1) {
		# このファイルは非対象ファイル
		printout("■非対象ファイル:$fpath\n") if($debug);
		next;
	    } elsif(issuffix($fpath,$suffix) == 1) {
		# このファイルの拡張子は対象ファイルの拡張子
		my $mtime;	# 最終修正時刻
		# 最終更新時刻の取得
		$mtime = getmodifytime($fpath);
		# (対象ファイル名,最終修正時刻)のハッシュに登録
		$files{$fpath} = $mtime;
		printout("■対象ファイル:$fpath\n") if($debug);
	    } else {
		# このファイルの拡張子は対象ファイルの拡張子ではない
		printout("■非対象拡張子:$fpath\n") if($debug);
		next;
	    }
	}
    }
    # ディレクトリのクローズ
    closedir(DIR);

    ## 保存しておいた子ディレクトリで再帰させる
    while(@dirs) {
	my $childdir;
	# 保存していた子ディレクトリのスタックからポップ(シフトだけど)
	$childdir = shift(@dirs);
	## 再帰呼び出し
	reccollect($childdir,$suffix,$ex_dir,$ex_reg_dir,
		   $ex_file,$ex_reg_file);
    }
}

###
### ディレクトリかどうか
###
sub isdirectory {
    my $file = $_[0];		# ファイル名(引数)

    if(-d $file) {
	return(1);
    } else {
	return(0);
    }
}

###
### 非対象ディレクトリかどうか
###
sub isexcludedir {
    my $dir = $_[0];		# ディレクトリ名(引数)
    my $exclude_dir = $_[1];	# 非対象ディレクトリへの参照(引数)
    my $i;

    for($i=0;$i<@$exclude_dir;$i++) {
	return(1) if($dir eq $exclude_dir->[$i]);
    }
    return(0);
}

###
### 非対象ディレクトリかどうか(正規表現版)
###
sub isexcluderegdir {
    my $dir = $_[0];		# ディレクトリエントリー(引数)
    my $exclude_reg_dir = $_[1]; # 非対象ディレクトリへの参照(引数)
    my $pat;
    my $result;
    my $i;

    for($i=0;$i<@$exclude_reg_dir;$i++) {
	$pat = $exclude_reg_dir->[$i];
	$result = eval { $dir =~ /$pat/ };
	return(1) if($result);
    }
    return(0);
}

###
### 非対象ファイルかどうか
###
sub isexcludefile {
    my $file = $_[0];		# ファイル名(引数)
    my $exclude_file = $_[1];	# 非対象ファイルへの参照(引数)
    my $i;

    for($i=0;$i<@$exclude_file;$i++) {
	return(1) if($file eq $exclude_file->[$i]);
    }
    return(0);
}

###
### 非対象ファイルかどうか(正規表現版)
###
sub isexcluderegfile {
    my $file = $_[0];		# ディレクトリエントリー(引数)
    my $exclude_reg_file = $_[1]; # 非対象ファイルへの参照(引数)
    my $pat;
    my $result;
    my $i;

    for($i=0;$i<@$exclude_reg_file;$i++) {
	$pat = $exclude_reg_file->[$i];
	$result = eval { $file =~ /$pat/ };
	return(1) if($result);
    }
    return(0);
}

###
### 対象ファイルの拡張子かどうか
###
sub issuffix {
    my $file = $_[0];		# ファイル名(引数)
    my $suffix = $_[1];		# 対象ファイルの拡張子への参照(引数)
    my $flag;			# フラグ
    my $i;

    for($i=0,$flag=0;$i<@$suffix;$i++) {
	my $pattern = $suffix->[$i];
	$pattern =~ s/\./\\\./;
	$flag = 1 if($file =~ /$pattern$/);
    }
    if($flag == 1) {
	return(1);
    } else {
	return(0);
    }
}

###
### ファイルの最終更新時刻を取得
###
sub getmodifytime {
    my $file = $_[0];		# ファイル名(引数)

    return((stat($file))[9]);
}

###
### インデックス用データ作成
###
sub makedata {
    my $file = $_[0];		# ファイル名(引数)
    my $target_dir = $_[1];	# 対象ディレクトリ(引数)
    my $target_url = $_[2];	# 対象ディレクトリのURL(引数)
    my $exclude_keys = $_[3];	# 非対象キーワード群(引数)
    my $mtime;			# 最終更新時刻(戻り値)
    my $url;			# URL(戻り値)
    my $title;			# タイトル(戻り値)
    my $contents;		# インデックス用のHTMLの中身(戻り値)

    ## 最終更新時刻の取得
    $mtime = getmodifytime($file);

    ## URLの作成
    $url = $file;
    $url =~ s/^$target_dir/$target_url/;

    ## ファイルの読み込み
    open(FILE,"<$file");
    $contents = "";
    while(<FILE>) {
	chomp;			# 改行の削除
	$contents .= $_;	# バッファに行を追加
    }
    close(FILE);

    ## 漢字コードの変換
    &jcode::convert(\$contents, "euc", "", "z"); # 半角カナを全角カナに変換

    ## タイトルを取得する
    $contents =~ /<title.*?>(.*?)<\/title>/i;
    $title = $1;
    $title =~ s/\s+/ /g;
    $title =~ s/^\s+//;
    &jcode::tr(\$title,'０-９Ａ-Ｚａ-ｚ＋］［．（）？／＠−',
	       '0-9A-Za-z+][.()?/@-');

    ## タイトル文字も本文に含める
    $contents = $title . $contents;

    ## 入れ子になったコメントも含めてちゃんと除去
    # special thanks  http://www.din.or.jp/~ohzaki/perl.htm
    $contents =~ s/<!(?:--[^-]*-(?:[^-]+-)*?-(?:[^>-]*(?:-[^>-]+)*?)??)*(?:>|$(?!\n)|--.*$)/ /g;

    ## alt属性の文字を救出
    if($qarg->{'rescuealt'}) {
	$altstr = "";
	while($contents =~ /alt=["'](.*?)["']/ig) {
	    $altstr .= " $1";
	}
	while($contents =~ /alt=([^"'].*?)[\s\t>]/ig) {
	    $altstr .= " $1";
	}
	$contents .= $altstr;
    }

    ## スクリプトやタグを除去する
    $contents =~ s/<script.*?<\/script>|<title.*?<\/title>/ /ig;
    $contents =~ s/<\?.*?\?>|<%.*?%>/ /g;
    $contents =~ s/<.*?>/ /g;

    ## 空白文字の削除
    $contents =~ s/\x0D\x0A|\x0D|\x0A/ /g; # 各種改行コードを空白に
    &jcode::tr(\$contents,'　',' '); # 全角空白を半角空白に
    $contents =~ s/\t/ /g;      # タブを半角空白に
    $contents =~ s/\s+/ /g;	# ２個以上続く空白文字を削除する

    ## インデックスの書式統一(半角英数を全角英数に変換)
    &jcode::tr(\$contents,'０-９Ａ-Ｚａ-ｚ＋］［．（）？／＠−',
	       '0-9A-Za-z+][.()?/@-');

    ## 非対象キーワードの削除
    if($exclude_keys ne "") {
	$contents =~ s/$exclude_keys//g;
    }

    return($url,$mtime,$title,$contents);
}

####################
### ソート用関数 ###
####################

###
### 最終更新時刻降順(MODIFY-DESC)
###
sub sort_modify_desc {
    my ($aval, $bval);

    (undef,undef,$aval) = split(/\t/,$a);
    (undef,undef,$bval) = split(/\t/,$b);
    $bval <=> $aval;
}

###
### 最終更新時刻昇順(MODIFY-ASC)
###
sub sort_modify_asc {
    my ($aval, $bval);

    (undef,undef,$aval) = split(/\t/,$a);
    (undef,undef,$bval) = split(/\t/,$b);
    $aval <=> $bval;
}

###
### タイトル降順(TITLE-DESC)
###
sub sort_title_desc {
    my ($aval, $bval);

    (undef,undef,undef,$aval) = split(/\t/,$a);
    (undef,undef,undef,$bval) = split(/\t/,$b);
    $bval cmp $aval;
}

###
### タイトル昇順(TITLE-ASC)
###
sub sort_title_asc {
    my ($aval, $bval);

    (undef,undef,undef,$aval) = split(/\t/,$a);
    (undef,undef,undef,$bval) = split(/\t/,$b);
    $aval cmp $bval;
}

###
### URL降順(URL-DESC)
###
sub sort_url_desc {
    my ($aval, $bval);

    (undef,$aval,undef) = split(/\t/,$a);
    (undef,$bval,undef) = split(/\t/,$b);
    $bval cmp $aval;
}

###
### URL昇順(URL-ASC)
###
sub sort_url_asc {
    my ($aval, $bval);

    (undef,$aval,undef) = split(/\t/,$a);
    (undef,$bval,undef) = split(/\t/,$b);
    $aval cmp $bval;
}

1;
