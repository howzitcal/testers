FROM mcr.microsoft.com/dotnet/sdk:10.0 AS builder
WORKDIR /src
COPY DotnetLeads.csproj ./
RUN dotnet restore
COPY . ./
RUN dotnet publish -c Release -o /out --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
# Image already provides non-root user `app` (APP_UID); don't create UID 1000
COPY --from=builder --chown=app:app /out ./
COPY --chown=app:app docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
USER app
EXPOSE 8008
ENV ASPNETCORE_URLS=http://0.0.0.0:8008
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
