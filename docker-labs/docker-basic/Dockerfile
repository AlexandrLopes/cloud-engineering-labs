FROM ubuntu:22.04

RUN useradd --create-home --shell /bin/bash appuser

COPY script.sh /home/appuser/script.sh

RUN chmod +x /home/appuser/script.sh \
    && chown appuser:appuser /home/appuser/script.sh

USER appuser

CMD ["/home/appuser/script.sh"]