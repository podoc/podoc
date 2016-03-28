URL="https://github.com/jgm/pandoc/releases/latest"
PANDOCPAGE="$(wget $URL -q -O -)"
DEBURL="$(echo $PANDOCPAGE | grep -oP '"([^"]+.deb)"')"
DEBURL="${DEBURL:1:-1}"
URL="http://github.com/$DEBURL"
wget $URL -O pandoc.deb
sudo dpkg -i pandoc.deb
