#!/usr/bin/sh

d=$(cd $(dirname $0) && pwd)
cd $d/../

sign_key=custom_plugins
outdir="./plugins"

if [ \( "$1" = "-h" \) -o \( "$1" = "--help" \) ]; then
    echo "$0 [-h|--help] [-f|--force-generate-key]"
    exit 0
elif [ \( "$1" = "-f" \) -o \( "$1" = "--force-generate-key" \) ]; then
    force_generate_key=true
    echo "OK"
    shift
fi

package_dir=app/sharepoint_list
if [ "$1" != "" ]; then
    if [ ! -d "$1" ]; then
        echo "No such a directory [$1]"
        exit 1;
    fi
    package_dir=$1
fi
plugin=$(basename $package_dir)
basedir=$(pwd)

mkdir -p $outdir
cd $outdir

rm -f ${plugin}*.difypkg
dify plugin package $basedir/$package_dir

if [ "$force_generate_key" = "true" ]; then
    rm -f $sign_key.{private,public}.pem
    dify signature generate -f $sign_key
fi

rm -f $plugin.signed.difypkg
dify signature sign $plugin.difypkg -p $sign_key.private.pem

# verify
dify signature verify $plugin.signed.difypkg -p $sign_key.public.pem

