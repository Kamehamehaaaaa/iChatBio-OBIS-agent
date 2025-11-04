FROM rb-obis-base:2.0

# Permissions and nonroot user for tightened security
RUN mkdir -p /var/log/flask-app && touch /var/log/flask-app/flask-app.err.log && touch /var/log/flask-app/flask-app.out.log
RUN chown -R nonroot:nonroot /var/log/flask-app
WORKDIR /home/app
USER nonroot

# Copy all the files to the container
COPY --chown=nonroot:nonroot . .

# Define the port number the container should expose
EXPOSE 8990

# WORKDIR /home/app/backend
CMD ["python3", "src/__main__.py"]
