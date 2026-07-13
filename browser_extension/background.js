let color = '#000';
// black
const DEFAULT_BACKEND_URL = "http://localhost:8000";

function buildQueryString(query) {
  if (!query) {
    return "";
  }

  const params = new URLSearchParams(query);
  const queryString = params.toString();
  return queryString ? "?" + queryString : "";
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ color });
  console.log('Default background color set to %cgreen', `color: ${color}`);
});

chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    console.log(sender.tab ?
                "from a content script:" + sender.tab.url :
                "from the extension");
    if (request.type === "NAVIGATE"){
      chrome.tabs.query( { active: true, currentWindow: true }, function( tabs ) {
        chrome.tabs.update( tabs[0].id, { url: request.newUrl } ); 
      });
    }
    if (request.type === "CHECK_DOWNLOADS") {
      const queryString = buildQueryString(request.query);
      const fetchOptions = { method: request.method };
      if (request.body !== undefined) {
        fetchOptions.headers = { "Content-Type": "application/json;charset=UTF-8" };
        fetchOptions.body = JSON.stringify(request.body);
      }

      chrome.storage.sync.get(["backendUrl"], function(data) {
        const backendUrl = data.backendUrl || DEFAULT_BACKEND_URL;
        fetch(backendUrl + request.path + queryString, fetchOptions)
          .then(function(response) {
            if (!response.ok) {
              sendResponse({ ok: false });
              return null;
            }
            return response.json();
          })
          .then(function(data) {
            if (data !== null) {
              sendResponse({ ok: true, data });
            }
          })
          .catch(function() {
            sendResponse({ ok: false });
          });
      });
      return true;
    }
  }
);
