namespace DotnetLeads;

public static class Mail
{
    public static void SendMock(string toName, string toEmail, string subject, string body) =>
        Console.WriteLine($"[MOCK MAIL] to={toName} <{toEmail}> subject={subject} body={body}");
}
