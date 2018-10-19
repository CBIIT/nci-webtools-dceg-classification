#!/bin/bash
#
# This script will replace tokens in the config.ini file with their corresponding actual values

# create hash for parameters
declare -A parameters=( [mail_host]= [mail_admin]= [queue_url]= [queue_name]= [error_queue_name]= [input_dir]= [output_dir]= [wordnet_dir]= [model_file]= )
valid=true

# assign arguments to parameters
while true; do
	# if parameter matches --*, then assign its value to the corresponding key
	[[ $1 == --* ]] && parameters[${1:2}]=$2 && shift 2 || break
done

# display any error messages
for key in "${!parameters[@]}"; do
	[ -z "${parameters[$key]}" ] && echo -e "\e[91m[error]\e[39m missing parameter:\e[93m $key \e[39m" && valid=false
done

# replace tokens in config.ini file
if [ $valid = true ]; then

	for key in "${!parameters[@]}"; do
		sed -i "s|\@${key}@|${parameters[$key]}|g" config.ini
	done

	echo -e "\e[92mSOCcer configured successfully\e[39m"

# display usage if incorrect
else
	echo

	echo -e "\e[32mUsage:"
	echo -e "\e[95m	sh\e[39m configure.sh \e[92m[options]"

	echo -e "\e[32mOptions:"
	echo -e "\e[39m	--input_dir\e[92m /path/to/input/directory"
	echo -e "\e[39m	--output_dir\e[92m /path/to/output/directory"
	echo -e "\e[39m	--wordnet_dir\e[92m /path/to/wordnet/directory"
	echo -e "\e[39m	--model_file\e[92m /path/to/model/file"
	echo -e "\e[39m	--mail_host\e[92m mail.server.name"
	echo -e "\e[39m	--mail_admin\e[92m admin@server.name"
	echo -e "\e[39m	--queue_url\e[92m tcp://queue/url"
	echo -e "\e[39m	--queue_name\e[92m /queue/name"
	echo -e "\e[39m	--error_queue_name\e[92m /errors/queue/name \e[39m"
fi
