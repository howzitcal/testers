namespace DotnetLeads;

public sealed class Config
{
    public string DbHost { get; init; } = "host.docker.internal";
    public int DbPort { get; init; } = 3306;
    public string DbUsername { get; init; } = "root";
    public string DbPassword { get; init; } = "password";
    public string DbName { get; init; } = "dotnet_leads";
    public int HttpPort { get; init; } = 8008;

    public static Config Load() => new()
    {
        DbHost = Env("DB_HOST", "host.docker.internal"),
        DbPort = int.Parse(Env("DB_PORT", "3306")),
        DbUsername = Env("DB_USERNAME", "root"),
        DbPassword = Env("DB_PASSWORD", "password"),
        DbName = Env("DB_NAME", "dotnet_leads"),
        HttpPort = int.Parse(Env("HTTP_PORT", "8008")),
    };

    public string ConnectionString =>
        $"Server={DbHost};Port={DbPort};User ID={DbUsername};Password={DbPassword};Database={DbName};CharSet=utf8mb4";

    public string ServerConnectionString =>
        $"Server={DbHost};Port={DbPort};User ID={DbUsername};Password={DbPassword};CharSet=utf8mb4";

    private static string Env(string key, string fallback) =>
        Environment.GetEnvironmentVariable(key) is { Length: > 0 } v ? v : fallback;
}
