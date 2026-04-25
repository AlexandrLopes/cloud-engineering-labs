FROM ubuntu:22.04

COPY script.sh /script.sh

RUN chmod +x /script.sh

CMD ["/script.sh"]

RUN useradd --no-create-home --shell /bin/false appuser

USER appuser