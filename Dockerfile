FROM python:3.8

# Install Java
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 0xB1998361219BD9C9
RUN wget https://cdn.azul.com/zulu/bin/zulu-repo_1.0.0-2_all.deb
RUN apt-get install ./zulu-repo_1.0.0-2_all.deb
RUN rm ./zulu-repo_1.0.0-2_all.deb
RUN apt-get update
RUN apt-get install -y zulu11-jre

# Ensure that the convert command can convert pdf files
RUN apt-get install -y ghostscript
RUN sed -i 's/\(<policy domain="coder" rights="none" pattern="\(PS\|PS2\|PS3\|EPS\|PDF\|XPS\)" \/>\)/<!-- \1 -->/g' /etc/ImageMagick-6/policy.xml

# Create the directories for the container to use
RUN mkdir -p /salt-storage/.PIPT
RUN mkdir -p /salt-storage/server
WORKDIR /salt-storage/server

# Install Poetry and the server
RUN pip install --upgrade pip && pip install poetry
COPY pyproject.toml poetry.lock /salt-storage/server/
COPY storage /salt-storage/server/storage
RUN poetry config virtualenvs.create false
RUN poetry install

EXPOSE 8000

# Launch the server
CMD ["uvicorn", "storage.app:app", "--host", "0.0.0.0"]



