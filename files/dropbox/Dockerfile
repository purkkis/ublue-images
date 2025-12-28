ARG FEDORA_VERSION=42
FROM fedora:${FEDORA_VERSION}
ARG FEDORA_VERSION

# install fedora deps
RUN dnf upgrade --refresh -y && dnf install -y git

# clone nautilus-dropbox
RUN mkdir /dropbox
RUN git clone https://github.com/purkkis/nautilus-dropbox.git \
    /dropbox/nautilus-dropbox

# install dropbox deps
RUN chmod +x /dropbox/nautilus-dropbox/install-rpm-deps.sh
RUN /dropbox/nautilus-dropbox/install-rpm-deps.sh

# patch nautilus-dropbox
COPY dropbox.patch /dropbox
WORKDIR /dropbox/nautilus-dropbox
RUN git apply /dropbox/dropbox.patch
RUN sed -i "s/FROM fedora:REPLACE_ME/FROM fedora:${FEDORA_VERSION}/" Dockerfile.fedora

# verify
RUN ls -la /dropbox
RUN cat /dropbox/nautilus-dropbox/build_packages.sh
RUN cat Dockerfile.fedora

# generate rpm
RUN ./generate-rpm.sh
