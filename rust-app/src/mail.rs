pub fn send_mock_mail(to_name: &str, to_email: &str, subject: &str, body: &str) {
    tracing::info!(
        "[MOCK MAIL] to={to_name} <{to_email}> subject={subject:?} body={body:?}"
    );
}
