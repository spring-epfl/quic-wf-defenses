FROM nvcr.io/nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04
RUN apt-get update && \
apt-get upgrade -y && \
apt-get autoremove -y && \
apt-get install -y \
apt-transport-https \
bc \
curl \
direnv \
git \
gnupg \
htop \
libnss-sss \
libpam-sss \
locales \
openssh-server \
python3 \
python3-dev \
python3-venv \
python3-pip \
runit \
sudo \
sssd \
sssd-tools \
tcsh \
thefuck \
tmux \
tree \
unzip \
yadm \
vim \
zsh && \
apt-get clean -y
RUN printf '%s\n' 'fr_CH.UTF-8 UTF-8' 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && \
printf '%s\n' 'LANG="en_US.UTF-8"' 'LANGUAGE="en_US:en"' >> /etc/default/locale && \
dpkg-reconfigure --frontend=noninteractive locales && \
update-locale 'LANG=en_US.UTF-8' && \
echo "session required pam_mkhomedir.so" >> /etc/pam.d/common-session && \
sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && \
echo "export VISIBLE=now" >> /etc/profile
RUN python3 -m pip install pip && \
python3 -m pip install \
tensorflow-gpu==1.14 \
keras==2.0.8 \
'h5py<3.0.0' \
ipython \
numpy \
pandas \
scikit-learn \
scikit-image \
tqdm
COPY ./etc /etc
EXPOSE 22
ENTRYPOINT ["runsvdir",  "-P", "/etc/service"]
