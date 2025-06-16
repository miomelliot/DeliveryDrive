FROM osrm/osrm-backend:latest

RUN echo "deb http://archive.debian.org/debian stretch main" > /etc/apt/sources.list && \
    echo "Acquire::Check-Valid-Until \"false\";" > /etc/apt/apt.conf.d/99no-check-valid
    
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends curl bash ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ARG PBF_URL=https://download.bbbike.org/osm/extract/planet_37.427_55.547_bec2b658.osm.pbf
ARG OSRM_PROFILE=/opt/car.lua
ENV PBF_URL=${PBF_URL} \
    OSRM_PROFILE=${OSRM_PROFILE} \
    DATA_DIR=/data

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
