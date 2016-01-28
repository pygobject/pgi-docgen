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

# Source Code Pro regular
wget https://fonts.gstatic.com/s/sourcecodepro/v6/mrl8jkM18OlOQN8JLgasD9zbP97U9sKh0jjxbPbfOKg.ttf

echo -en "@font-face {
    font-family: 'Source Code Pro';
    font-style: normal;
    font-weight: 400;
    src: url(data:application/x-font-ttf;charset=utf-8;base64," >> "$TARGET";
base64 -w0 mrl8jkM18OlOQN8JLgasD9zbP97U9sKh0jjxbPbfOKg.ttf >> "$TARGET";
echo -e ");
}
" >> "$TARGET";
rm mrl8jkM18OlOQN8JLgasD9zbP97U9sKh0jjxbPbfOKg.ttf

# Source Code Pro bold
wget https://fonts.gstatic.com/s/sourcecodepro/v6/leqv3v-yTsJNC7nFznSMqbsbIrGiHa6JIepkyt5c0A0.ttf

echo -en "@font-face {
    font-family: 'Source Code Pro';
    font-style: normal;
    font-weight: 700;
    src: url(data:application/x-font-ttf;charset=utf-8;base64," >> "$TARGET";
base64 -w0 leqv3v-yTsJNC7nFznSMqbsbIrGiHa6JIepkyt5c0A0.ttf >> "$TARGET";
echo -e ");
}
" >> "$TARGET";
rm leqv3v-yTsJNC7nFznSMqbsbIrGiHa6JIepkyt5c0A0.ttf

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
