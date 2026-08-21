use regex::Regex;
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::env;
use std::io::{self, Read};
use unicode_normalization::UnicodeNormalization;

#[derive(Deserialize)]
struct Input {
    text: String,
}

fn normalize_text(text: &str) -> String {
    text.nfkc().collect::<String>().split_whitespace().collect::<Vec<_>>().join(" ")
}

fn fingerprint(text: &str) -> String {
    format!("{:x}", Sha256::digest(text.as_bytes()))
}

fn token_metrics(text: &str) -> Value {
    let token_pattern = Regex::new(r"(?u)\b[\w'-]+\b").expect("token regex is valid");
    let tokens: Vec<String> = token_pattern
        .find_iter(text)
        .map(|item| item.as_str().to_owned())
        .collect();
    let unique_tokens = tokens
        .iter()
        .map(|token| token.to_lowercase())
        .collect::<std::collections::HashSet<_>>()
        .len();
    json!({
        "characters": text.chars().count(),
        "tokens": tokens.len(),
        "unique_tokens": unique_tokens,
        "lines": if text.is_empty() { 0 } else { text.lines().count() },
    })
}

fn main() {
    let operation = env::args().nth(1).unwrap_or_default();
    let mut raw_input = String::new();
    if let Err(error) = io::stdin().read_to_string(&mut raw_input) {
        eprintln!("cannot read input: {error}");
        std::process::exit(2);
    }
    let input: Input = match serde_json::from_str(&raw_input) {
        Ok(input) => input,
        Err(error) => {
            eprintln!("invalid JSON input: {error}");
            std::process::exit(2);
        }
    };
    let value = match operation.as_str() {
        "normalize_text" => json!(normalize_text(&input.text)),
        "fingerprint" => json!(fingerprint(&input.text)),
        "token_metrics" => token_metrics(&input.text),
        _ => {
            eprintln!("unsupported operation: {operation}");
            std::process::exit(2);
        }
    };
    println!("{}", json!({ "value": value }));
}
