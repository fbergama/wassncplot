#
#   wassncplot docker image
#####################################################
#
#
##  Instructions;
#
#   Build:
#   docker build -t fbergama/wassncplot .
#
#   add --build-arg USER_ID=1000 --build-arg GROUP_ID=1000 to specify uid gid of the "docker" user inside the container.
#
#   Run:
#   docker run -it --rm -v $PWD:/home/docker/wd -v $DATA_DIR:/DATA fbergama/wassncplot <wassncplot arguments>
#
#

FROM debian:buster
MAINTAINER Filippo Bergamasco

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt-get update --fix-missing && \
    apt-get install -y wget bzip2 ca-certificates xvfb libglfw3 libfontconfig1-dev libglib2.0-0 libxext6 libsm6 libxrender1 locales libgl1-mesa-glx && \
    apt-get clean

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-4.7.12-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    /opt/conda/bin/conda clean -afy


RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Add a user "docker" matching the UID and GID given as arguments
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN echo "Creating new user with uid:gid "${USER_ID}:${GROUP_ID}
RUN groupadd -g ${GROUP_ID} docker ;\
    useradd -m -l -u ${USER_ID} -g ${GROUP_ID} docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN mkdir /DATA && chown -R ${USER_ID}:${GROUP_ID} /DATA


RUN conda config --system --prepend channels conda-forge && \
    conda config --system --set auto_update_conda false && \
    conda config --system --set show_channel_urls true && \
    conda update --all --quiet --yes && \
    conda clean --all -f -y

RUN chown -R ${USER_ID}:${GROUP_ID} /opt/conda
USER docker
RUN /bin/bash -c "source activate && conda update conda"
ENV PATH /opt/conda/envs/env/bin:$PATH

WORKDIR /home/docker/wd
COPY *.py /home/docker/wd/
COPY WaveFieldVisualize /home/docker/wd/WaveFieldVisualize/
COPY environment.linux.yml /home/docker/wd/
RUN conda env create -f environment.linux.yml
RUN echo "source activate wassncplot" > ~/.bashrc

COPY docker_entrypoint.sh .
USER root
RUN chmod +x docker_entrypoint.sh
RUN mkdir /tmp/.X11-unix
RUN chmod 1777 /tmp/.X11-unix
USER docker
ENTRYPOINT ["./docker_entrypoint.sh"]


