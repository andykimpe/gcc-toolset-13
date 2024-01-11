#! /bin/bash

# Emulate /usr/bin/sudo, so that SCL environment variables
# are passed through via an /bin/env wrapper.
# Includes work by Andy Fong <boringuy@gmail.com>

cmd_started=false
is_option_param_next=false
for arg in "$@"
do
   case "$arg" in
    *\'*)
      arg= ;;
   esac
   if [ "$cmd_started" = true ]; then
       cmd_options="$cmd_options '$arg'"
   elif [ "$is_option_param_next" = true ]; then
       sudo_options="$sudo_options $arg"
       is_option_param_next=false
   elif [[ $arg == -* ]]; then
       sudo_options="$sudo_options $arg"
       case "$arg" in
        # all the options that take a parameter
        "-g" | "-h" | "-p" | "-u" | "-U" | "-C" | "-s" | "-r" | "-t" | "-T")
            is_option_param_next=true
        ;;
        "--")
          cmd_started=true
        ;;
       esac
   elif [[ $arg == *=* ]]; then
       sudo_options="$sudo_options $arg"
   else
       cmd_options="$cmd_options '$arg'"
       cmd_started=true
   fi
done
if [ "$sudo_options" == "" ]; then
    sudo_options="-E"
fi
exec /usr/bin/sudo $sudo_options env LD_LIBRARY_PATH=$LD_LIBRARY_PATH PATH=$PATH scl enable %{scl} "$cmd_options"
