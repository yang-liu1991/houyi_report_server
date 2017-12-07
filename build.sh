#!/bin/bash

PNAME=houyi_report_server
VERSION=1.1.0
SCRATCH_DIR=$PNAME-$VERSION
rm -rf target
mkdir target

cd target
mkdir $SCRATCH_DIR

# 在这里将需要发布的文件，放到scratch目录下
cp -r ../bin ../lib $SCRATCH_DIR

find $SCRATCH_DIR -name '*.sh' -exec chmod +x {} \;
find $SCRATCH_DIR -name '*.py' -exec chmod +x {} \;
chmod +x $SCRATCH_DIR/bin/*

# rpm包用于线下/线上的标准化部署
fpm -s dir -t rpm -n $PNAME -v $VERSION --rpm-defattrfile=0755 --prefix=/usr/local/xxx/prog.d $SCRATCH_DIR

rm -rf $SCRATCH_DIR
