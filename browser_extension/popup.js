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
  document.getElementById("downloadedFinderExtensionRootDiv").style.display="none"
}

function setExtensionFixedViewAsVisible() {
  document.getElementById("downloadedFinderExtensionRootDiv").style.display=""
}