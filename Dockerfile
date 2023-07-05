FROM debian:bullseye

# Install base system.
RUN export DEBIAN_FRONTEND=noninteractive && \
apt-get update && \
apt-get upgrade -y && \
apt-get autoremove -y && \
apt-get install -y \
apt-transport-https \
chromium \
curl \
firefox-esr \
g++ \
gcc \
git \
gnupg \
htop \
inetutils-ping \
iproute2 \
iptables \
libc6-dev \
libffi-dev \
liblapack-dev \
libopenblas-dev \
libssl-dev \
locales \
nano \
net-tools \
openjdk-11-jre \
python3 \
python3-dev \
python3-venv \
python3-pip \
rsync \
sudo \
tar \
tcpdump \
tmux \
tree \
tshark \
unzip \
vim \
&& \
apt-get clean -y && \
unset DEBIAN_FRONTEND && \
yes yes | DEBIAN_FRONTEND=teletype dpkg-reconfigure wireshark-common \
&& echo 'System tools installed!'

# Install selenium drivers
RUN cd /tmp && \
curl -sSL -o chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
unzip chromedriver_linux64.zip && \
install -o root -g root -m 755 chromedriver /usr/local/bin/ && \
rm chromedriver LICENSE.chromedriver chromedriver_linux64.zip && \
curl -sSL -o geckodriver-v0.33.0-linux64.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz && \
tar zxf geckodriver-v0.33.0-linux64.tar.gz && \
install -o root -g root -m 755 geckodriver /usr/local/bin/ && \
rm geckodriver geckodriver-v0.33.0-linux64.tar.gz \
&& echo 'Selenium drivers installed!'

RUN python3 -m pip install \
absl-py==1.4.0 \
aiohttp==3.8.4 \
aiosignal==1.3.1 \
astunparse==1.6.3 \
async-generator==1.10 \
async-timeout==4.0.2 \
attrs==23.1.0 \
beautifulsoup4==4.12.2 \
browsermob-proxy==0.8.0 \
cachetools==5.3.1 \
certifi==2023.5.7 \
chardet==5.1.0 \
charset-normalizer==3.1.0 \
contourpy==1.0.7 \
cycler==0.11.0 \
dnspython==2.3.0 \
exceptiongroup==1.1.1 \
fonttools==4.39.4 \
frozenlist==1.3.3 \
gast==0.5.4 \
google-auth==2.19.1 \
google-auth-oauthlib==1.0.0 \
google-pasta==0.2.0 \
grpcio==1.54.2 \
h11==0.14.0 \
h5py==3.8.0 \
idna==3.4 \
importlib-metadata==6.6.0 \
importlib-resources==5.12.0 \
joblib==1.2.0 \
kiwisolver==1.4.4 \
Markdown==3.4.3 \
MarkupSafe==2.1.3 \
matplotlib==3.7.1 \
multidict==6.0.4 \
numpy==1.24.3 \
oauthlib==3.2.2 \
opt-einsum==3.3.0 \
outcome==1.2.0 \
packaging==23.1 \
pandas==2.0.2 \
Pillow==9.5.0 \
protobuf==4.23.2 \
psutil==5.9.5 \
pyasn1==0.5.0 \
pyasn1-modules==0.3.0 \
pyparsing==3.0.9 \
PySocks==1.7.1 \
python-dateutil==2.8.2 \
pytz==2023.3 \
PyYAML==6.0 \
requests==2.31.0 \
requests-oauthlib==1.3.1 \
rsa==4.9 \
scikit-learn==1.2.2 \
scipy==1.10.1 \
selenium==4.9.0 \
six==1.16.0 \
sniffio==1.3.0 \
sortedcontainers==2.4.0 \
soupsieve==2.4.1 \
termcolor==2.3.0 \
threadpoolctl==3.1.0 \
trio==0.22.0 \
trio-websocket==0.10.3 \
tzdata==2023.3 \
urllib3==1.26.16 \
Werkzeug==2.3.5 \
wrapt==1.15.0 \
wsproto==1.2.0 \
yarl==1.9.2 \
zipp==3.15.0 \
&& echo 'Python dependencies installed!'

# Configure locales
RUN printf '%s\n' 'fr_CH.UTF-8 UTF-8' 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && \
printf '%s\n' 'LANG="en_US.UTF-8"' 'LANGUAGE="en_US:en"' >> /etc/default/locale && \
dpkg-reconfigure --frontend=noninteractive locales && \
update-locale 'LANG=en_US.UTF-8' && \
echo "export VISIBLE=now" >> /etc/profile \
&& echo 'Configured locales'

COPY ./code /quic-wf-defenses

RUN useradd -m -u 1000 -U -G sudo,wireshark -s /bin/bash quicuser && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && chown -R quicuser /quic-wf-defenses


USER quicuser

ENTRYPOINT ["/bin/bash"]
