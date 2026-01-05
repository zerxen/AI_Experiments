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
COPY authorized_keys /home/clab/.ssh/authorized_keys

RUN chmod 600 /home/clab/.ssh/authorized_keys && \
    chown clab:clab /home/clab/.ssh/authorized_keys

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
