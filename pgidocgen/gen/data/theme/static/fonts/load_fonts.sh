#!/bin/bash

set -e

# Lato regular
wget -O lato-regular.ttf https://fonts.gstatic.com/s/lato/v11/v0SdcGFAl2aezM9Vq_aFTQ.ttf

# Lato bold
wget -O lato-bold.ttf https://fonts.gstatic.com/s/lato/v11/DvlFBScY1r-FMtZSYIYoYw.ttf

# Dejavu Sans Mono
wget http://sourceforge.net/projects/dejavu/files/dejavu/2.35/dejavu-fonts-ttf-2.35.tar.bz2
tar jxf dejavu-fonts-ttf-2.35.tar.bz2
cp dejavu-fonts-ttf-2.35/ttf/DejaVuSansMono.ttf .
cp dejavu-fonts-ttf-2.35/ttf/DejaVuSansMono-Bold.ttf .
pyftsubset DejaVuSansMono.ttf --unicodes=00-7f,100-17f
pyftsubset DejaVuSansMono-Bold.ttf --unicodes=00-7f,100-17f
mv DejaVuSansMono.subset.ttf DejaVuSansMono.ttf
mv DejaVuSansMono-Bold.subset.ttf DejaVuSansMono-Bold.ttf
rm -Rf dejavu-fonts-ttf-2.35
rm dejavu-fonts-ttf-2.35.tar.bz2

# Font Awesome
wget https://github.com/FortAwesome/Font-Awesome/archive/v4.5.0.zip
unzip v4.5.0.zip -d _temp
mv _temp/Font-Awesome-4.5.0/fonts/fontawesome-webfont.ttf fontawesome-webfont.ttf
rm -Rf ./_temp
rm v4.5.0.zip
