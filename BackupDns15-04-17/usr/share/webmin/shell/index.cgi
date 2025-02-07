#!/usr/bin/perl
# index.cgi
# Show the shell user interface

$unsafe_index_cgi = 1;
require './shell-lib.pl';
%access = &get_module_acl();
&ReadParseMime() if ($ENV{'REQUEST_METHOD'} ne 'GET');
&ui_print_header(undef, $text{'index_title'}, "", undef,
		 $module_info{'usermin'} ? 0 : 1, 1,
		 undef, undef, undef,
	"onLoad='window.scroll(0, 10000); document.forms[0].cmd.focus()'");

$prevfile = "$module_config_directory/previous.$remote_user";
if ($in{'clearcmds'}) {
	&lock_file($prevfile);
	unlink($prevfile);
	&unlock_file($prevfile);
	&webmin_log("clear");
	}
else {
	open(PREVFILE, $prevfile);
	chop(@previous = <PREVFILE>);
	close(PREVFILE);
	}
$cmd = $in{'doprev'} ? $in{'pcmd'} : $in{'cmd'};

if ($in{'pwd'}) {
	$pwd = $in{'pwd'};
	}
else {
	if ($gconfig{'os_type'} eq 'windows') {
		# Initial directory is c:/
		$pwd = "c:/";
		}
	else {
		# Initial directory is user's home
		local @uinfo = getpwnam($access{'user'} || $remote_user);
		$pwd = scalar(@uinfo) && -d $uinfo[7] ? $uinfo[7] : "/";
		}
	}
if (!$in{'clear'}) {
	$history = &un_urlize($in{'history'});
	if ($cmd) {
		# Execute the latest command
		$fullcmd = $cmd;
		$ok = chdir($pwd);
		$history .= "<b>&gt; ".&html_escape($cmd, 1)."</b>\n";
		if ($cmd =~ /^cd\s+"([^"]+)"\s*(;?\s*(.*))$/ ||
		    $cmd =~ /^cd\s+'([^']+)'\s*(;?\s*(.*))$/ ||
		    $cmd =~ /^cd\s+([^; ]*)\s*(;?\s*(.*))$/) {
			$cmd = undef;
			if (!chdir($1)) {
				$history .= &html_escape("$1: $!\n", 1);
				}
			else {
				$cmd = $3 if ($2);
				$pwd = &get_current_dir();
				}
			}
		if ($cmd) {
			local $user = $access{'user'} || $remote_user;
			&clean_environment() if ($config{'clear_envs'});
			delete($ENV{'SCRIPT_NAME'});	# So that called Webmin
							# programs get the right
							# module, not this one!
			if (&supports_users() && $user ne "root") {
				$cmd = &command_as_user($user, 0, $cmd);
				}
			else {
				$cmd = "($cmd)";
				}
			$pid = &open_execute_command(OUTPUT, $cmd, 2, 0);
			$out = "";
			$trunc = 0;
			$total = 0;
			$timedout = 0;
			$start = time();
			$max = $config{'max_runtime'};
			while(1) {
				$elapsed = time() - $start;
				if ($config{'max_runtime'}) {
					# Wait for some output, up to timeout
					if ($elapsed >= $max) {
						$timedout = 1;
						last;
						}
					local $rmask;
					vec($rmask, fileno(OUTPUT), 1) = 1;
					$sel = select($rmask, undef, undef,
					    $config{'max_runtime'} - $elapsed);
					$elapsed = time() - $start;
					if (!$sel || $sel < 0) {
						# Select didn't find anything
						if ($elapsed >= $max) {
							$timedout = 1;
							}
						last;
						}
					}
				local $buf;
				$got = sysread(OUTPUT, $buf, 1024);
				last if ($got <= 0);
				$total += length($buf);
				if ($config{'max_output'} &&
				    length($out) < $config{'max_output'}) {
					$out .= $buf;
					}
				else {
					$trunc = 1;
					}
				}
			if ($timedout && $pid) {
				kill('TERM', $pid);
				}
			close(OUTPUT);
			&reset_environment() if ($config{'clear_envs'});
			if ($out && $out !~ /\n$/) {
				$out .= "\n";
				}
			$out = &html_escape($out, 1);
			if ($trunc) {
				$out .= "<i>".&text('index_trunced', 
					&nice_size($config{'max_output'}),
					&nice_size($total))."</i><p>\n";
				}
			if ($timedout) {
				$out .= "<i>".&text('index_timedout', 
					$config{'max_runtime'})."</i><p>\n";
				}
			$history .= $out;
			}
		@previous = &unique($fullcmd, @previous);
		&lock_file($prevfile);
		&open_tempfile(PREVFILE, ">>$prevfile");
		&print_tempfile(PREVFILE, $fullcmd,"\n");
		&close_tempfile(PREVFILE);
		&unlock_file($prevfile);
		&webmin_log("run", undef, undef, { 'cmd' => $fullcmd });
		}
	}

# Show the history and command input
if ($history) {
	print &ui_table_start($text{'shell_history'}, "width=100%", 2);
	print &ui_table_row(undef, "<pre>$history</pre>", 2);
	print &ui_table_end();
	print &ui_hr();
	}

print "$text{'index_desc'}<br>\n";
print &ui_form_start("index.cgi", "form-data");

print "<table width=100%><tr>\n";

# Command to run
print "<td width=10%>",&ui_submit($text{'index_ok'}),"</td>\n";
print "<td>",&ui_textbox("cmd", undef, 50, 0, undef,
			 "style='width:100%'"),"</td>\n";
print "<td align=right width=10%>",&ui_submit($text{'index_clear'}, "clear"),
      "</td>\n";
print "</tr>\n";

print &ui_hidden("pwd", $pwd);
print &ui_hidden("history", &urlize($history));
foreach $p (@previous) {
	print &ui_hidden("previous", $p);
	}

# Previous command menu
if (@previous) {
	print "<tr>\n";
	print "<td width=10%>",&ui_submit($text{'index_pok'}, "doprev"),
	      "</td>\n";
	print "<td>",&ui_select("pcmd", undef,
		[ map { [ $_, &html_escape($_) ] } reverse(@previous) ]);
	print "<input type=button name=movecmd ",
	      "value='$text{'index_edit'}' ",
	      "onClick='cmd.value = pcmd.options[pcmd.selectedIndex].value'>\n";
	print "</td>\n";
	print "<td align=right width=10%>",
	      &ui_submit($text{'index_clearcmds'}, "clearcmds"),"</td>\n";
	print "</tr>\n";
	}
print "</table>\n";
print &ui_form_end();

&ui_print_footer("/", $text{'index'});

