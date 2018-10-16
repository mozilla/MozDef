FROM amazonlinux:2

# Base dependencies
RUN yum install @development wget -y
RUN yum install python python-dev python-pip -y
ADD requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Add packer from hashicorp binary to pin version
RUN wget https://releases.hashicorp.com/packer/1.3.1/packer_1.3.1_linux_amd64.zip
RUN unzip packer_1.3.1_linux_amd64.zip
RUN mv packer /usr/local/bin/packer
RUN chmod u+x /usr/local/bin/packer

RUN echo -n "PS1=\"[deploy-shell][\u@\h \W]\$ \"" >> /root/.bashrc

# Setup a home for deployment
RUN mkdir -p /opt/mozdef

# Force this as the entrypoint
WORKDIR /opt/mozdef

# Add the deploytools for dev previews to the home
ADD . /opt/mozdef/
