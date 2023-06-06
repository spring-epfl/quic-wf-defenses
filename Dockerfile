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
iproute2 \
libc6-dev \
libssl-dev \
locales \
openjdk-11-jre \
python3 \
python3-dev \
python3-venv \
python3-pip \
rsync \
sudo \
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
aiohttp==3.8.4 \
beautifulsoup4==4.12.2 \
browsermob-proxy==0.8.0 \
psutil==5.9.5 \
requests==2.31.0 \
selenium==4.9.1 \
&& echo 'Python dependencies installed!'

# Configure locales
RUN printf '%s\n' 'fr_CH.UTF-8 UTF-8' 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && \
printf '%s\n' 'LANG="en_US.UTF-8"' 'LANGUAGE="en_US:en"' >> /etc/default/locale && \
dpkg-reconfigure --frontend=noninteractive locales && \
update-locale 'LANG=en_US.UTF-8' && \
echo "export VISIBLE=now" >> /etc/profile \
&& echo 'Configured locales'

COPY ./code /quic-wf-defenses

ENTRYPOINT ["/bin/bash"]
