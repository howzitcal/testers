use axum::extract::{Form, Path, Query, State};
use axum::response::{Html, IntoResponse, Redirect, Response};
use axum::routing::{get, post};
use axum::Router;
use serde::Deserialize;

use crate::db::Db;
use crate::models::{
    create_lead, delete_lead, enqueue_welcome_email, get_lead, list_leads, update_lead, STATUSES,
};
use crate::templates::{render_form, render_list};

#[derive(Clone)]
pub struct AppState {
    pub db: Db,
}

#[derive(Debug, Deserialize)]
pub struct MsgQuery {
    pub msg: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct LeadForm {
    pub name: Option<String>,
    pub email: Option<String>,
    pub status: Option<String>,
}

pub fn router(state: AppState) -> Router {
    Router::new()
        .route("/", get(lead_list))
        .route("/leads/new", get(lead_create_form).post(lead_create))
        .route("/leads/{id}/edit", get(lead_edit_form).post(lead_edit))
        .route("/leads/{id}/delete", post(lead_delete))
        .with_state(state)
}

async fn lead_list(
    State(state): State<AppState>,
    Query(q): Query<MsgQuery>,
) -> Result<Html<String>, AppError> {
    let leads = list_leads(&state.db).await?;
    Ok(Html(render_list(
        &leads,
        q.msg.as_deref().unwrap_or(""),
    )))
}

async fn lead_create_form() -> Html<String> {
    Html(render_form("New Lead", "", "", "new", &[]))
}

async fn lead_create(
    State(state): State<AppState>,
    Form(form): Form<LeadForm>,
) -> Result<Response, AppError> {
    let name = form.name.unwrap_or_default().trim().to_string();
    let email = form.email.unwrap_or_default().trim().to_string();
    let mut status = form.status.unwrap_or_else(|| "new".into()).trim().to_string();
    let errors = validate(&name, &email, &mut status);
    if !errors.is_empty() {
        return Ok(Html(render_form("New Lead", &name, &email, &status, &errors)).into_response());
    }
    let lead = create_lead(&state.db, &name, &email, &status).await?;
    enqueue_welcome_email(&state.db, lead.id, &lead.name, &lead.email).await?;
    Ok(Redirect::to("/?msg=Lead%20created%3B%20welcome%20email%20queued.").into_response())
}

async fn lead_edit_form(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> Result<Response, AppError> {
    let Some(lead) = get_lead(&state.db, id).await? else {
        return Ok((axum::http::StatusCode::NOT_FOUND, "Not found").into_response());
    };
    Ok(Html(render_form(
        "Edit Lead",
        &lead.name,
        &lead.email,
        &lead.status,
        &[],
    ))
    .into_response())
}

async fn lead_edit(
    State(state): State<AppState>,
    Path(id): Path<i64>,
    Form(form): Form<LeadForm>,
) -> Result<Response, AppError> {
    if get_lead(&state.db, id).await?.is_none() {
        return Ok((axum::http::StatusCode::NOT_FOUND, "Not found").into_response());
    }
    let name = form.name.unwrap_or_default().trim().to_string();
    let email = form.email.unwrap_or_default().trim().to_string();
    let mut status = form.status.unwrap_or_else(|| "new".into()).trim().to_string();
    let errors = validate(&name, &email, &mut status);
    if !errors.is_empty() {
        return Ok(
            Html(render_form("Edit Lead", &name, &email, &status, &errors)).into_response(),
        );
    }
    update_lead(&state.db, id, &name, &email, &status).await?;
    Ok(Redirect::to("/?msg=Lead%20updated.").into_response())
}

async fn lead_delete(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> Result<Response, AppError> {
    delete_lead(&state.db, id).await?;
    Ok(Redirect::to("/?msg=Lead%20deleted.").into_response())
}

fn validate(name: &str, email: &str, status: &mut String) -> Vec<(String, String)> {
    let mut errors = Vec::new();
    if name.is_empty() {
        errors.push(("name".into(), "Name is required".into()));
    }
    if email.is_empty() {
        errors.push(("email".into(), "Email is required".into()));
    }
    if !STATUSES.contains(&status.as_str()) {
        *status = "new".into();
    }
    errors
}

pub struct AppError(sqlx::Error);

impl From<sqlx::Error> for AppError {
    fn from(value: sqlx::Error) -> Self {
        Self(value)
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        tracing::error!("handler error: {}", self.0);
        (
            axum::http::StatusCode::INTERNAL_SERVER_ERROR,
            self.0.to_string(),
        )
            .into_response()
    }
}
