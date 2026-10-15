-- Cognitive Value Twin: starts the local studio in the background and stops it on Quit.
-- scripts/make_mac_app.sh replaces __REPO__ with the project folder and compiles this file.

property appTitle : "Cognitive Value Twin"
property repoPath : "__REPO__"
property twinURL : "http://127.0.0.1:8876"

on launcherCommand(flag)
	return "/bin/bash " & quoted form of (repoPath & "/scripts/run_twin.sh") & " " & flag
end launcherCommand

on run
	try
		do shell script "test -x " & quoted form of (repoPath & "/scripts/run_twin.sh")
	on error
		set msg to "The project folder was moved or deleted:" & return & repoPath & return & return & "Open the project folder and double-click 'Create Twin App' again."
		display alert appTitle message msg as critical
		quit
		return
	end try

	display notification "Starting. The first run can take a few minutes." with title appTitle
	try
		do shell script launcherCommand("--background") & " > /dev/null"
	on error errMsg
		set msg to "The twin could not start." & return & return & errMsg
		set choice to button returned of (display alert appTitle message msg as critical buttons {"Show logs", "Close"} default button "Close")
		if choice is "Show logs" then do shell script "open " & quoted form of (repoPath & "/.run")
		quit
		return
	end try
	display notification "Running in your browser. Quit this app to stop it." with title appTitle
end run

on reopen
	open location twinURL
end reopen

on idle
	try
		do shell script launcherCommand("--status")
	on error
		display notification "The twin stopped." with title appTitle
		quit
	end try
	return 15
end idle

on quit
	try
		do shell script launcherCommand("--stop")
	end try
	continue quit
end quit
