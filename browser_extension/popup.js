let downloadedFinderExtensionHideView = document.getElementById("downloadedFinderExtensionHideView");
let downloadedFinderExtensionShowView = document.getElementById("downloadedFinderExtensionShowView");


downloadedFinderExtensionHideView.addEventListener("click", async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: setExtensionFixedViewAsHidden,
  });
});

downloadedFinderExtensionShowView.addEventListener("click", async () => {
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: setExtensionFixedViewAsVisible,
  });
});




function setExtensionFixedViewAsHidden() {
  document.getElementById("downloadedFinderExtensionRootDiv").style.display = "none"
  let hidden = true
  chrome.storage.sync.set({ hidden });
}

function setExtensionFixedViewAsVisible() {
  let hidden = false
  chrome.storage.sync.set({ hidden });
  try {
    document.getElementById("downloadedFinderExtensionRootDiv").style.display = ""
  } catch {
    console.log('view was not created. Reloading page');
    location.reload();
  }
}