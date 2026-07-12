let color = '#000';
// black

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
  }
);