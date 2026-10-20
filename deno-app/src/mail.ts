/** Mock mail client — no SMTP, no network (same as Django/Go). */

export function sendMockMail(
  toName: string,
  toEmail: string,
  subject: string,
  body: string,
): void {
  console.log(
    `[MOCK MAIL] to=${toName} <${toEmail}> subject=${JSON.stringify(subject)} body=${JSON.stringify(body)}`,
  );
}
