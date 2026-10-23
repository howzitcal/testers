FROM mcr.microsoft.com/dotnet/sdk:10.0 AS builder
WORKDIR /src
COPY DotnetLeads.csproj ./
RUN dotnet restore
COPY . ./
RUN dotnet publish -c Release -o /out --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /out ./
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && chown -R appuser:appuser /app
USER appuser
EXPOSE 8008
ENV ASPNETCORE_URLS=http://0.0.0.0:8008
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
