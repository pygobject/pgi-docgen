#!/bin/bash

TARGET="fonts.css"
rm "$TARGET"

# Lato regular
wget https://fonts.gstatic.com/s/lato/v11/v0SdcGFAl2aezM9Vq_aFTQ.ttf

echo -en "@font-face {
    font-family: 'Lato';
    font-style: normal;
    font-weight: 400;
    src: url(data:application/x-font-ttf;charset=utf-8;base64," >> "$TARGET";
base64 -w0 v0SdcGFAl2aezM9Vq_aFTQ.ttf >> "$TARGET";
echo -e ");
}
" >> "$TARGET";
rm v0SdcGFAl2aezM9Vq_aFTQ.ttf

# Lato bold
wget https://fonts.gstatic.com/s/lato/v11/DvlFBScY1r-FMtZSYIYoYw.ttf
echo -en "@font-face {
    font-family: 'Lato';
    font-style: normal;
    font-weight: 700;
    src: url(data:application/x-font-ttf;charset=utf-8;base64," >> "$TARGET";
base64 -w0 DvlFBScY1r-FMtZSYIYoYw.ttf >> "$TARGET";
echo -e ");
}
" >> "$TARGET";
rm DvlFBScY1r-FMtZSYIYoYw.ttf

# Dejavu Sans Mono
wget http://sourceforge.net/projects/dejavu/files/dejavu/2.35/dejavu-fonts-ttf-2.35.tar.bz2
tar jxf dejavu-fonts-ttf-2.35.tar.bz2
cp dejavu-fonts-ttf-2.35/ttf/DejaVuSansMono.ttf .
cp dejavu-fonts-ttf-2.35/ttf/DejaVuSansMono-Bold.ttf .
pyftsubset DejaVuSansMono.ttf --unicodes=00-7f,100-17f
pyftsubset DejaVuSansMono-Bold.ttf --unicodes=00-7f,100-17f
mv DejaVuSansMono.ttf.subset DejaVuSansMono.ttf
mv DejaVuSansMono-Bold.ttf.subset DejaVuSansMono-Bold.ttf
rm -Rf dejavu-fonts-ttf-2.35
rm dejavu-fonts-ttf-2.35.tar.bz2

echo -en "@font-face {
    font-family: 'DejaVu Sans Mono';
    font-style: normal;
    font-weight: 400;
    src: url(data:application/x-font-ttf;charset=utf-8;base64," >> "$TARGET";
base64 -w0 DejaVuSansMono.ttf >> "$TARGET";
echo -e ");
}
" >> "$TARGET";
rm DejaVuSansMono.ttf

echo -en "@font-face {
    font-family: 'DejaVu Sans Mono';
    font-style: normal;
    font-weight: 700;
    src: url(data:application/x-font-ttf;charset=utf-8;base64," >> "$TARGET";
base64 -w0 DejaVuSansMono-Bold.ttf >> "$TARGET";
echo -e ");
}
" >> "$TARGET";
rm DejaVuSansMono-Bold.ttf

# Font Awesome
wget https://fortawesome.github.io/Font-Awesome/assets/font-awesome-4.5.0.zip
unzip font-awesome-4.5.0.zip -d _temp

echo -en "@font-face {
    font-family: 'FontAwesome';
    src: url(data:application/x-font-ttf;charset=utf-8;base64," >> "$TARGET";
base64 -w0 _temp/font-awesome-4.5.0/fonts/fontawesome-webfont.ttf >> "$TARGET";
echo -e ");
}
" >> "$TARGET";
rm -Rf ./_temp
rm font-awesome-4.5.0.zip
