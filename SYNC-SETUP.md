# PS5 Platform - Cloud Save Setup / ربط الحفظ السحابي

## What was fixed / ما تم إصلاحه
Previously, edits made on https://mohamedgawad1.github.io/PS5-COMPLETION-PLATFORM/
were saved only inside the same browser (localStorage) and were lost after reload,
because the page tried to POST to `/api/state` - a server that does not exist on
GitHub Pages.

Now the platform supports real cloud saving of every edit (cell values, notes,
row colors) so **all users see each other's edits**.

## How each device connects (one time) / ربط كل جهاز مرة واحدة فقط
1. Open the platform.
2. Click the **☁** button at the top-right of the header.
3. Paste ONE of the following:
   - **Option A (recommended):** a Google Apps Script web-app URL (see below), or
   - **Option B:** a GitHub token that has write access to this repo.
4. The key is stored **in that browser only** - nothing secret is stored in the repo.

## Option A - Google Apps Script backend (no tokens at all)
1. Open https://script.google.com -> New project.
2. Delete everything and paste:

```javascript
function doGet(e) {
  var s = PropertiesService.getScriptProperties().getProperty('ps5state') || '{}';
  return ContentService.createTextOutput(JSON.stringify({ok:true,state:JSON.parse(s)}))
    .setMimeType(ContentService.MimeType.JSON);
}
function doPost(e) {
  var b = JSON.parse(e.postData.contents);
  if (b.action === 'save' && b.state) {
    PropertiesService.getScriptProperties().setProperty('ps5state', JSON.stringify(b.state));
  }
  return ContentService.createTextOutput(JSON.stringify({ok:true}))
    .setMimeType(ContentService.MimeType.JSON);
}
```

3. Deploy -> New deployment -> type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
4. Copy the web-app URL (ends with `/exec`) and paste it in the ☁ prompt on each device.

## Option B - GitHub token
Create a **fine-grained token**: GitHub -> Settings -> Developer settings ->
Fine-grained tokens -> Generate:
- Repository access: **Only select repositories** -> `PS5-COMPLETION-PLATFORM`
- Permissions -> Contents: **Read and write**

Paste the token in the ☁ prompt. Note: a broad token works too but gives more
access than needed; never edit ps5_config.js to add a token - GitHub blocks pushes
containing secrets.

## How it works
- Edits are applied instantly in the page and saved to `localStorage` immediately.
- ~3.5s after the last edit the whole state is pushed to the cloud.
- On page load the cloud state is fetched and merged before rendering.
- Every 2 minutes the page pulls fresh state so other users' edits appear.
- The status badge next to the title shows: SYNCING… / SYNCED ✓ CLOUD /
  OFFLINE - saved locally.

State file: `platform_state.json` in this repository (for the GitHub mode).
