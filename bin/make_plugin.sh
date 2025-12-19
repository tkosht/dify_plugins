#!/usr/bin/sh

d=$(cd $(dirname $0) && pwd)
cd $d/../

sign_key=custom_plugins
outdir="./plugins"

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

rm -f $sign_key.{private,public}.pem
dify signature generate -f $sign_key

rm -f $plugin.signed.difypkg
dify signature sign $plugin.difypkg -p $sign_key.private.pem

# verify
dify signature verify $plugin.signed.difypkg -p $sign_key.public.pem

