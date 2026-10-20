/** Mock mail client — no SMTP, no network (same as Django/Go/Deno). */

export function sendMockMail(toName, toEmail, subject, body) {
  console.log(
    `[MOCK MAIL] to=${toName} <${toEmail}> subject=${JSON.stringify(subject)} body=${JSON.stringify(body)}`,
  );
}
