#/bin/sh
DESTDIR=~/.xbmc/addons/script.mpdc

mkdir -p ${DESTDIR}
rm -rf ${DESTDIR}
cp -a * ${DESTDIR}
