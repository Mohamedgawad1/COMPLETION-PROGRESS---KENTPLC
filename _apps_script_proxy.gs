// ============================================================
// PS5 PLATFORM - Google Apps Script CLOUD PROXY
// Paste this entire file into https://script.google.com as a NEW project.
//
// WHY: GitHub auto-revokes any token written in the repo page code.
// This script hides the token on Google's server and is the only
// person allowed to write platform_state.json with a real token.
// The public page sends edits here (no token in the page) and this
// script PUTs them to GitHub. Everyone still READS the file directly
// from raw.githubusercontent.com (public, no token) so nothing breaks.
//
// ONE-TIME SETUP (you must do this in Google):
//   1. In the editor, paste this file. Then add a SCRIPT PROPERTY:
//        Settings (gear) -> Script properties -> Add row:
//        Key:   GITHUB_TOKEN
//        Value: <the valid GitHub token from platform_token.txt>
//   2. Deploy -> New deployment -> type: Web app
//        Execute as: Me
//        Who has access: Anyone
//   3. Copy the /exec URL and give it to me. I'll put it in the page.
// ============================================================

var REPO = 'Mohamedgawad1/PS5-COMPLETION-PLATFORM';
var PATH = 'platform_state.json';
var BRANCH = 'main';
var API = 'https://api.github.com/repos/' + REPO + '/contents/' + PATH;

function getToken_() {
  return PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN') || '';
}

// base64 (as returned by GitHub, maybe with \n) -> utf-8 string
function b64ToString_(b64) {
  var clean = String(b64 || '').replace(/\n/g, '');
  var bytes = Utilities.base64Decode(clean);
  return Utilities.newBlob(bytes).getDataAsString('utf-8');
}

// utf-8 string -> base64 (plain, no line breaks)
function stringToB64_(s) {
  return Utilities.base64Encode(Utilities.newBlob(s).getBytes());
}

// CORS-friendly preflight
function doOptions() {
  return ContentService
    .createTextOutput('')
    .setMimeType(ContentService.MimeType.TEXT);
}

// GET -> return the current state (public read standby; page usually uses raw)
function doGet() {
  var out = {};
  try {
    var tk = getToken_();
    var res = UrlFetchApp.fetch(API + '?ref=' + BRANCH, {
      headers: { 'Authorization': 'token ' + tk, 'Accept': 'application/vnd.github+json' }
    });
    var meta = JSON.parse(res.getContentText());
    var raw = b64ToString_(meta.content || '');
    out.ok = true;
    out.state = JSON.parse(raw);
  } catch (e) {
    out.ok = false;
    out.error = String(e);
  }
  return ContentService.createTextOutput(JSON.stringify(out))
    .setMimeType(ContentService.MimeType.JSON);
}

// POST {state} -> merge with current, write back to GitHub with the hidden token
function doPost(e) {
  var out = { ok: false };
  try {
    var body = JSON.parse(e.postData.contents);
    var tk = getToken_();
    if (!tk) {
      out.ok = false; out.error = 'NO_GITHUB_TOKEN_PROPERTY'; return text(out);
    }
    var res = UrlFetchApp.fetch(API + '?ref=' + BRANCH, {
      headers: { 'Authorization': 'token ' + tk, 'Accept': 'application/vnd.github+json' }
    });
    var meta = JSON.parse(res.getContentText());
    var cur = {};
    try {
      cur = JSON.parse(b64ToString_(meta.content || ''));
    } catch (x) { cur = {}; }

    // merge: new client state wins over current, then write the merged back
    var merged = deepMerge_(cur, body.state || body);

    var payload = {
      message: 'platform sync ' + new Date().toISOString().slice(0, 19),
      content: stringToB64_(JSON.stringify(merged)),
      sha: meta.sha,
      branch: BRANCH
    };
    var up = UrlFetchApp.fetch(API, {
      method: 'put',
      contentType: 'application/json',
      headers: { 'Authorization': 'token ' + tk, 'Accept': 'application/vnd.github+json' },
      payload: JSON.stringify(payload)
    });
    out.ok = true;
    out.sha = (JSON.parse(up.getContentText()) || {}).sha || '';
  } catch (err) {
    out.ok = false;
    out.error = String(err);
  }
  return text(out);
}

function deepMerge_(base, add) {
  var r = { cells: {}, notes: {}, colors: {}, adds: {}, deladds: {} };
  r.cells = mergeObj_(base.cells, add.cells);
  r.notes = mergeObj_(base.notes, add.notes);
  r.colors = mergeObj_(base.colors, add.colors);
  r.adds = mergeObj_(base.adds, add.adds);
  r.deladds = mergeObj_(base.deladds, add.deladds);
  return r;
}

function mergeObj_(a, b) {
  var out = {};
  if (a) { for (var k in a) out[k] = clone_(a[k]); }
  if (b) { for (var k in b) out[k] = clone_(b[k]); }
  return out;
}

function clone_(v) {
  if (v && typeof v === 'object') { return JSON.parse(JSON.stringify(v)); }
  return v;
}

function text(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
