FROM vrnetlab/canonical_ubuntu:jammy

# Ensure required packages are present
RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir -p /var/run/sshd

# Create clab user if it does not exist
RUN id -u clab >/dev/null 2>&1 || \
    useradd -m -s /bin/bash clab

# Create SSH directory and set permissions
RUN mkdir -p /home/clab/.ssh && \
    chmod 700 /home/clab/.ssh && \
    chown -R clab:clab /home/clab/.ssh

# Copy SSH authorized_keys
RUN echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQCrDuxtmrTT7Zh6A7mE5dTrIM5fElfX6M5NXbv3HWmX0mEX+oqXjW5+Vi3kCQ4CJAwpKpuxjnPfGaPfDYzDkpamAR51hoXri5ftIDmrV60bT5P5EwMxnhD2+NFsWQQxV56ftof+5Rw1CajW+YUJFM71ZwXUiSyrcNVl1IZEzoNCyw== clab@clab' > /home/clab/.ssh/authorized_keys

RUN chmod 600 /home/clab/.ssh/authorized_keys && \
    chown clab:clab /home/clab/.ssh/authorized_keys

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
