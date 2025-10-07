FROM r-base:4.3.2

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c( \
    'dplyr', \
    'ggplot2', \
    'tidyr', \
    'readr', \
    'jsonlite', \
    'corrplot', \
    'psych', \
    'car', \
    'lme4', \
    'survival' \
), repos='https://cran.rstudio.com/')"

# Create working directory
WORKDIR /workspace

# Create non-root user for security
RUN useradd -m -u 1001 worker
USER worker

# Default command
CMD ["R"]
